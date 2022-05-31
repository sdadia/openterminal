from typing import Literal

import dotenv
from prompt_toolkit.history import FileHistory
from rich import console
from prompt_toolkit import PromptSession

dotenv.load_dotenv()

console = console.Console()
session = PromptSession(
    enable_history_search=True, history=FileHistory(".session_history")
)


def findFutureValue(
    principle: int,
    numYears: int,
    rateOfCompounding: float,
    compoundingFreq: Literal[
        "daily", "monthly", "quaterly", "semiannually", "annually"
    ],
) -> float:

    compoundingFreqMapping = dict(zip([
        "daily", "monthly", "quaterly", "semiannually", "annually"
    ],
    [365, 12, 4, 2, 1]))
    M = rateOfCompounding/compoundingFreqMapping[compoundingFreq]
    print(M)

    finalValue: float = principle * (1+(rateOfCompounding*0.01)/M)**(M*numYears)
    return finalValue



ans = findFutureValue(10e3, 2, rateOfCompounding=8.0, compoundingFreq='quaterly')
print(f'{ans:,}')
