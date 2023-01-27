"""
pysim
-----
A simple interface for running simulink models from Python

This assumes that the MATLAB engine is installed and that the MATLAB engine
is in the system path.
The parameters for the simulink model should be defined in the MATLAB
workspace. The model should also contain `To Workspace` blocks for the
signals that you want to log.
"""

# Imports from standard library
from typing import Union, Dict
from pathlib import Path

# Imports from third party packages
from matlab import engine
from rich import print
import numpy as np


class Simulink:
    """
    Interface for running Simulink models

    Attributes
    ----------=
    name : str
        Name of the model
    eng : matlab.engine.MatlabEngine
        MATLAB engine

    Methods
    -------
    connect()
        Connect to MATLAB engine, if not already connected
    disconnect()
        Disconnect from MATLAB engine
    set_params(params: Dict[str, Union[str, float, int]])
        Set model parameters
    run(start: int=0, stop: int=30)
        Run model
    """

    def __init__(
        self, 
        path: Union[str, Path], 
        outvars: list=['tout'], 
        connect: bool=True
    ) -> None:
        """
        Constructor for Simulink class

        Parameters
        ----------
        path : Union[str, Path]
            Path to the .slx file
        outvars : list
            List of output variables from the model. 
            These should be accessible via `out.<outvar>` in MATLAB. 
            `tout` is automatically added to the list of output variables.
        connect : bool
            Connect to MATLAB engine on initialization, by default True
        """

        self.__path = Path(path)
        if not self.__path.exists():
            raise FileNotFoundError(f"Path '{path}' does not exist")
        
        self.__name = self.__path.stem

        self.outvars = np.unique(outvars + ['tout']).tolist()

        if connect:
            self.connect()
        
    def connect(self) -> None:
        """
        Connect to MATLAB engine if not already connected and load the model
        """

        if not hasattr(self, '__engine'):
            print("[bold green]Connecting to MATLAB engine...[/bold green]")
            self.__engine = engine.start_matlab()
            self.eng.addpath(str(self.__path.parent), nargout=0)

            print("[bold green]Loading model...[/bold green]")
            self.eng.eval(f"model = '{self.name}';", nargout=0)
            self.eng.load_system(self.name, nargout=0)
        else:
            print("[bold yellow]MATLAB engine already running.[/bold yellow]")

    def disconnect(self) -> None:
        """
        Disconnect from MATLAB engine
        """

        if hasattr(self, '__engine'):
            print("[bold green]Disconnecting from MATLAB engine...[/bold green]")
            self.eng.close_system(self.name, nargout=0)
            self.eng.quit()
            del self.__engine
        else:
            print("[bold yellow]MATLAB engine not running.[/bold yellow]")

    def set_params(self, params: Dict[str, Union[str, float, int]]) -> None:
        """
        Set model parameters

        Parameters
        ----------
        params : Union[str, float, int]
            Dictionary of model parameters. Keys are the parameter names and
            values are the parameter values.
        """

        cmd = ""
        for key, value in params.items():
            if isinstance(value, str):
                value = f"'{value}'"
            cmd += f"{key} = {value}; "

        self.eng.eval(cmd, nargout=0)

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

        # Run simulation
        cmd = f"""
        set_param(model, 'StartTime', '{start}', 'StopTime', '{stop}');
        out = sim(model);
        """
        self.eng.eval(cmd, nargout=0)

        # Read output variables
        out = {}
        for var in self.outvars:
            try:
                self.eng.eval(f"{var} = out.{var};", nargout=0)
                out[var] = np.asarray(self.eng.workspace[var]).flatten()
            except:
                print(f"[bold red]Could not read '{var}'[/bold red]")

        return out

    @property
    def name(self) -> str:
        """Name of the model"""
        return self.__name
    
    @property
    def eng(self) -> engine.matlabengine.MatlabEngine:  # type: ignore
        """MATLAB engine"""
        return self.__engine

    def __str__(self) -> str:
        return f"Simulink model: {self.name}"
    
    def __repr__(self) -> str:
        return f"Simulink('{self.__path}')"
    
    def __enter__(self) -> 'Simulink':
        return self
    
    def __exit__(self, *args) -> None:
        self.disconnect()
    
    def __del__(self) -> None:
        self.disconnect()
