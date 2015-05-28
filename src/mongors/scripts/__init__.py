import re
import click
from itertools import imap

from mongors import checks, rs, utils


re_addr_port = re.compile(r"(?P<addr>[^:]*)(?::(?P<port>\d*))?")


def cli():
    common(obj={})


def sanitize_instances(ctx, param, value):
    """Sanitize instances: add default port and remove duplicates."""

    instances = []

    for address, port in (
            re_addr_port.match(instance).groups()
            for instance in value
    ):
        port = port and port or 27017
        if not (address, port) in instances:
            instances.append((address, port))

    return instances


@click.group()
@click.option("--timeout", "-t", type=click.FLOAT, default=10.0,
              help="Timeout to wait for each instance to get up.")
@click.option("instances", '--instance', '-i', multiple=True,
              required=True,
              callback=sanitize_instances,
              help="Replica set instances.")
@click.pass_context
def common(ctx, instances, timeout):
    states = checks.wait_for_instances(*instances, timeout=timeout)

    if not states[False]:
        click.echo(click.style("Instances are ready for replica set.", fg="green"), err=True)
        ctx.obj['instances'] = instances

    else:
        click.echo(
            click.style(
                "Some instances are not up and running: {}"
                .format(', '.join(':'.join(imap(str, state))
                                  for state in states[False])), fg="red"),
            err=True
        )
        exit(1)


@common.command(help="Initiate and return a json status of the replicaset.")
@click.argument("name", required=True)
@click.option("--reconfig", "-r", is_flag=True, help="Reconfig an invalid replica set.")
@click.pass_context
def ensure(ctx, name, reconfig):
    replica_set = rs.ReplicaSet(name, *ctx.obj['instances'])
    try:
        status = replica_set.ensure(reconfig=reconfig)
        click.echo(utils.dumps(status))
        click.echo(click.style("Replica set up and running", fg="green"), err=True)

    except rs.ReplicaSetInvalid:
        click.echo(click.style("Replica set is invalid! Try --reconfig option!", fg="red"))
        exit(1)
