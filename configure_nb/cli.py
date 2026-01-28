import typer

configure_nb = typer.Typer()


@configure_nb.command()
def main():
    """
    Generate a valid .env file for Neurobagel deployment configuration.
    """
    print("Hello from configure-nb!")
