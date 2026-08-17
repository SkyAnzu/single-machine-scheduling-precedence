import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENCODING_DIR = PROJECT_ROOT / "Encoding"
TEST_DIR = PROJECT_ROOT / "Test"
FILENAMES_DIR = PROJECT_ROOT / "Filenames"
DATA_2013_DIR = PROJECT_ROOT / "2013"
DATA_2016_DIR = PROJECT_ROOT / "2016"
INS_DIR = DATA_2016_DIR / "Ins"
OUTPUT_DIR = DATA_2016_DIR
LICENSE_FILE = PROJECT_ROOT / "gurobi.lic"

DATASET_SIZES = [10, 20, 30, 40, 50]
INSTANCE_TYPES = ["S", "L"]
AVAILABLE_SOLVERS = [
    "seqcounter",
    "seqcardenc",
    "seqcardenc_ver2",
    "seqcardenc_ver2e",
    "seqcardenc_ver3",
    "seqcardenc_ver5",
    "seqcardenc_ver5_cadical300",
    "seqcardenc_ver5e",
    "seqcardenc_ver5e_cadical300",
    "seqcardenc_ver5e_1",
    "seqcardenc_ver5e_1_cadical300",
    "seqcardenc_ver4_1",
    "seqcardenc_ver4_2",
    "seqcardenc_ver4_3",
    "basicsat",
    "pbenc",
    "gurobi",
    "cpsat",
    "cplex_cp",
    "cplex_mp",
]
DEFAULT_SOLVERS = ["seqcounter", "gurobi"]


def configure_runtime_environment():
    encoding_path = str(ENCODING_DIR)
    if encoding_path not in sys.path:
        sys.path.insert(0, encoding_path)

    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if LICENSE_FILE.exists():
        os.environ["GRB_LICENSE_FILE"] = str(LICENSE_FILE)
