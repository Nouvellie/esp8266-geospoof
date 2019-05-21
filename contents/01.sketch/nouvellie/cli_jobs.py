import os
from pathlib import Path
from os.path import join

import pandas as pd
import click

from app.models.data_types import WiFiNet
from app.utils.net_parser import NetParser
from app.utils import scan_utils, logger_utils, file_utils, wigle_utils, data_utils
from app.settings import app_cfg as cfg

@click.group(chain=True)
@click.option('-v', '--verbose', 'opt_verbosity', count=True, default=4,
              show_default=True,
              help='Verbosity: -v DEBUG, -vv INFO, -vvv WARN, -vvvv ERROR, -vvvvv CRITICAL')
@click.pass_context
def cli(ctx, opt_verbosity):
    logger_utils.Logger.create(verbosity=opt_verbosity)
    ctx.obj['log'] = logger_utils.Logger.getLogger()

@cli.command('wigle_api', short_help='Fetches Wigle API data')
@click.option('-j', '--jobs', 'opt_fp_jobs',
              default=cfg.FP_JOBS_WIGLE_API,
              help='Job file (CSV)')
@click.option('--wigle_api_name', 'opt_api_name', envvar='WIGLE_API_NAME', required=True,
              help='Wigle API name (typically 35 chars)')
@click.option('--wigle_api_key', 'opt_api_key',  envvar='WIGLE_API_KEY', required=True,
              help='Wigle API token (typically 35 chars)')
@click.option('-f', '--force', 'opt_force', is_flag=True,
              help='Force overwrite file')
@click.pass_context
def cmd_wigle_api(ctx, opt_fp_jobs, opt_api_name, opt_api_key, opt_force):

    log = ctx.obj['log']
    if not (opt_api_key or opt_api_key):
        log.error('Wigle API Name and API key missing')
        return

    net_parser = NetParser()
    wigle = wigle_utils.WigleAPI(opt_api_name, opt_api_key)

    log.info('opening: {}'.format(opt_fp_jobs))
    jobs = pd.read_csv(opt_fp_jobs)
    jobs['comment'] = jobs['comment'].fillna('') 
    jobs['comment'] = jobs['comment'].astype('str')

    for i, job in jobs.iterrows():
        try:
            if int(job['run']) == 0:
                continue
        except Exception as e:
            log.warn(
                'Failed to read row. You may have extra rows in your CSV file.')
            continue  
        log.info(
            'Fetching lat: {lat}, long: {lon}, since: {since}, radius: {radius}'.format(**job))

        url = wigle.build_url(job.lat, job.lon, job.radius, job.since)
        networks = wigle.fetch(url, job.lat, job.lon)
        networks = net_parser.sort_distance(networks, 'wigle')

        meta = dict(job.copy()) 
        meta['type'] = 'wigle'  
        data = {'meta': meta, 'networks': networks}
        if Path(job.filepath).exists() and not opt_force:
            log.error(
                'file exists "{}". use "-f" to overwrite'.format(job.filepath))
        else:
            file_utils.write_json(data, job.filepath, minify=False)

@cli.command('wigle_export', short_help='Processed Exported Wigle data')
@click.option('-j', '--jobs', 'opt_fp_jobs',
              default=cfg.FP_JOBS_WIGLE_EXPORT,
              help='Job file (CSV)')
@click.option('-f', '--force', 'opt_force', is_flag=True,
              help='Force overwrite file')
@click.pass_context
def cmd_wigle(ctx, opt_fp_jobs, opt_force):

    log = ctx.obj['log']
    net_parser = NetParser()

    df_jobs = pd.read_csv(opt_fp_jobs, skiprows=(0))
    df_jobs['comment'] = df_jobs['comment'].fillna('').astype('str')

    for i, job in df_jobs.iterrows():
        if int(job['run']) == 0:
            continue

        fp_wigle = join(job.path_in, f'{job.filename}.csv')
        networks = net_parser.wigle_export_to_networks(
            fp_wigle, job.path_out, job.comment)
        networks = net_parser.sort_distance(networks, 'wigle_export')

        meta = dict(job.copy()) 
        meta['type'] = 'wigle_export' 
        data = {'meta': meta, 'networks': networks}
        if Path(job.filename).exists() and not opt_force:
            log.error(
                'file exists "{}". use "-f" to overwrite'.format(job.filename))
        else:
            file_utils.write_json(data, job.filename, minify=False)

@cli.command('ios')
@click.option('-j', '--jobs', 'opt_fp_jobs', required=True,
              default=cfg.FP_JOBS_IOS,
              help='Job file (CSV)')
@click.option('-o', '--output', 'opt_dir_out',
              default=cfg.DIR_NETWORKS,
              help='Path to networks output directory')
@click.option('-f', '--force', 'opt_force', is_flag=True,
              help='Force overwrite file')
@click.pass_context
def cmd_ios(ctx, opt_fp_jobs, opt_dir_out, opt_force):

    log = ctx.obj['log']
    parser = NetParser()

    log.info('opening: {}'.format(opt_fp_jobs))
    jobs = pd.read_csv(opt_fp_jobs)

    for i, job in jobs.iterrows():
        if int(job['run']) == 0:
            continue
        fp_ios = job.filepath
        networks = parser.ios_to_networks(fp_ios, job['lat'], job['lon'])
        meta = dict(job.copy())  
        meta['type'] = 'ios' 
        data = {'meta': meta, 'networks': networks}
        fp_out = join(job['path_out'], Path(job.filename).name)
        if Path(fp_out).exists() and not opt_force:
            log.error('file exists "{}". use "-f" to overwrite'.format(fp_out))
        else:
            file_utils.write_json(data, fp_out, minify=False)

@cli.command('arduino')
@click.option('-j', '--jobs', 'opt_fp_jobs', required=True,
              default=cfg.FP_JOBS_ARDUINO,
              help='Job file (CSV)')
@click.option('--sketch', 'opt_dir_sketch', required=True,
              type=click.Path(exists=True),
              help='Path to location summary file (Arduino .h')
@click.option('-f', '--force', 'opt_force', is_flag=True,
              help='Force overwrite file')
@click.pass_context
def cmd_arduino(ctx, opt_fp_jobs, opt_dir_sketch, opt_force):
    log = ctx.obj['log']
    net_parser = NetParser()
    opt_dir_sketch = str(opt_dir_sketch)

    log.info('opening: {}'.format(opt_fp_jobs))
    jobs = pd.read_csv(opt_fp_jobs)
    locations = []
    num_locations = 0
    num_networks = 0 

    for i, job in jobs.iterrows():
        if int(job['run']) == 0:
            continue
        log.info(job.filepath)
        location = file_utils.load_json(job.filepath)
        networks = location['networks']
        networks = net_parser.filter_rssi(
            networks, job['rssi_min'], job['rssi_max'])
        networks = net_parser.filter_channel(
            networks, job['channel_min'], job['channel_max'])
        networks = net_parser.sort_distance(networks, location['meta']['type'])
        networks = networks[:int(job['max_networks'])]
        location['networks'] = networks
        num_networks += len(networks)
        locations.append(location)
        ino_txt = net_parser.networks_to_arduino(
            location, job['name'], job['location'])

        fp_out = join(opt_dir_sketch, 'networks', f"{Path(job.filepath).stem}.h")
        if Path(fp_out).exists() and not opt_force:
            log.error('file exists "{}". use "-f" to overwrite'.format(fp_out))
        else:
            file_utils.write_text(ino_txt, fp_out)
        num_locations += 1
    location_summary_txt = net_parser.summarize_locations(locations)
    if opt_dir_sketch:
        fp_out = join(opt_dir_sketch, 'networks.h')
    else:
        fp_out = join(cfg.DIR_ARDUINO, 'networks.h')
    file_utils.write_text(location_summary_txt, fp_out)

    if opt_dir_sketch:

        fp_sketch_main = join(opt_dir_sketch, f'{Path(opt_dir_sketch).name}.ino')
        with open(fp_sketch_main, 'r') as fp:
            sketch_data = fp.readlines()
        sketch_data = [x.strip() for x in sketch_data]

        for i, code_line in enumerate(sketch_data):
            if 'const unsigned int NPLACES' in code_line:
                log.info(f'updated NPLACES = {num_locations}')
                sketch_data[i] = f'const unsigned int NPLACES = {num_locations};'
            if 'const unsigned int NNETS' in code_line:
                log.info(f'updated NNETS = {num_networks}')
                sketch_data[i] = f'const unsigned int NNETS = {num_networks};'
        with open(fp_sketch_main, 'w') as fp:
            fp.write('\n'.join(sketch_data))

if __name__ == '__main__':
    cli(obj={})
