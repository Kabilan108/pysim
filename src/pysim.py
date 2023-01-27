"""
Interface for running Simulink models
"""

# Imports from standard library
from typing import Union, List, Dict, Tuple, Optional
from pathlib import Path

# Imports from third party packages
from matlab import engine
from rich import print
import matplotlib.pyplot as plt
import numpy as np


class Simulink:
    """
    Interface for running Simulink models

    This assumes that the MATLAB engine is installed and that the MATLAB engine
    is in the system path.
    The parameters for the simulink model should be defined in the MATLAB
    workspace. The model should also contain `To Workspace` blocks for the
    signals that you want to plot.

    Attributes
    ----------

    Methods
    -------

    """

    def __init__(self, path: Union[str, Path], outvars: list) -> None:
        """
        Constructor for Simulink class

        Parameters
        ----------
        path : Union[str, Path]
            Path to the .slx file
        outvars : list
            List of output variables from the model. These should be accessible
            in the via `out.<outvar>` in MATLAB. `tout` is automatically added
            to the list of output variables.
        """

        # Convert path to Path object
        self.path = Path(path)

        # Validate path
        if not self.path.exists():
            raise FileNotFoundError(f"Path '{path}' does not exist")
        
        # Model name
        self.name = self.path.stem

        # Store Output variables
        self.outvars = np.unique(outvars + ['tout']).tolist()
        
    def connect(self) -> None:
        """
        Connect to MATLAB engine
        """

        print("[bold green]Starting MATLAB engine...[/bold green]")
        self.eng = engine.start_matlab()
        self.eng.addpath(self.path.parent.as_posix(), nargout=0)  # type: ignore
        return

    def modelInit(self, params: Dict[str, Union[str, float, int]]) -> None:
        """
        Initialize model and set parameters

        Parameters
        ----------
        params : Union[str, float, int]
            Dictionary of model parameters. Keys are the parameter names and
            values are the parameter values.
        """

        # Load model
        print("[bold green]Loading model...[/bold green]")
        self.eng.eval(f"model = '{self.name}';", nargout=0)  # type: ignore
        self.eng.load_system(self.name, nargout=0)  # type: ignore

        print("[bold green]Setting model parameters...[/bold green]")
        cmd = ""
        for key, value in params.items():
            if isinstance(value, str):
                value = f"'{value}'"
            cmd += f"{key} = {value}; "

        self.eng.eval(cmd, nargout=0)  # type: ignore

    def run(self, start: int=0, stop: int=30) -> dict:
        """
        Run model

        Parameters
        ----------
        start : int
            Start time of simulation, by default 0
        stop : int
            Stop time of simulation, by default 30
        """

        # Run the simulation
        self.eng.eval(  # type: ignore
            (f"set_param(model, 'StartTime', '{start}', 'StopTime', '{stop}'); "
             f"out = sim(model);"),
            nargout=0
        )

        # Read output variables
        print("[bold green]Reading output variables...[/bold green]")
        out = {}
        for var in self.outvars:
            try:
                self.eng.eval(f"{var} = out.{var};", nargout=0)  # type: ignore
                out[var] = np.asarray(self.eng.workspace[var]).flatten()  # type: ignore
            except:
                print(f"[bold red]Could not read '{var}'[/bold red]")

        return out

    def _sim_status(self) -> str:
        """Get simulation status"""
        return self.eng.get_param(self.name, 'SimulationStatus')  # type: ignore
