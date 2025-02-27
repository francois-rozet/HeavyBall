from typing import List

import torch
import torch.backends.opt_einsum
import typer
from torch import nn

from benchmark.utils import trial, loss_win_condition
from heavyball.utils import set_torch

app = typer.Typer(pretty_exceptions_enable=False)
set_torch()


class Model(nn.Module):
    def __init__(self, size=1024):
        super().__init__()
        self.param = nn.Parameter(torch.randn(size))
        # Create scales with condition number 1e12
        self.register_buffer('scales', torch.logspace(-6, 6, size))

    def forward(self):
        """Test optimizer's ability to handle poorly-conditioned problems."""
        return (self.param * self.scales).square().sum()


@app.command()
def main(method: List[str] = typer.Option(['qr'], help='Eigenvector method to use (for SOAP)'),
         dtype: List[str] = typer.Option(['float32'], help='Data type to use'), steps: int = 100,
         weight_decay: float = 0, opt: List[str] = typer.Option(['ForeachSOAP'], help='Optimizers to use'),
         trials: int = 100, win_condition_multiplier: float = 1.0, ):
    dtype = [getattr(torch, d) for d in dtype]
    model = Model().cuda().double()

    def data():
        return None, None

    # Very lenient win condition due to extreme condition number (1e12)
    trial(model, data, None, loss_win_condition(win_condition_multiplier * 1e-3), steps * 2, opt[0], dtype[0], 1, 1,
          weight_decay, method[0], 1, 1, failure_threshold=10, base_lr=1e-4, trials=trials)  # Lower lr, more steps and attempts


if __name__ == '__main__':
    app()
