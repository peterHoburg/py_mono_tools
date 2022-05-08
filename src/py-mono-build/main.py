import click


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@click.group()
def cli():
    pass


@cli.command()
def build():
    pass


@cli.command()
def deploy():
    pass


@cli.command(name="format")
def format_():
    pass


@cli.command()
def init():
    pass


@cli.command()
def lint():
    pass


@cli.group()
def new():
    pass


@new.command()
def migration():
    pass


@new.command()
def package():
    pass


@cli.command()
def run():
    pass


@cli.command()
def setup():
    pass


@cli.command()
def test():
    pass


@cli.command()
def validate():
    pass


if __name__ == '__main__':
    cli()
