import argparse
from pathlib import Path
import yaml
import wandb

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, required=True, help="Path where to save the models"
    )
    parser.add_argument(
        "--info",
        type=str,
        required=True,
        help="Path to the file with the pet information (i.e., image paths and pet ids)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to the sweep config file (.yaml)",
    )

    args = parser.parse_args()

    with open(args.config, "r") as f:
        sweep_config = yaml.safe_load(f)

    sweep_config["parameters"]["model_path"] = {
        "distribution": "constant",
        "value": args.model,
    }
    sweep_config["parameters"]["info_path"] = {
        "distribution": "constant",
        "value": args.info,
    }

    # TODO: Add SGD to sweep
    # Figure out how to only select the relevant optimizer params before sweep
    # At the moment, it will try to make runs with dampening, momentum and nesterov
    # when using Adam/AdamW

    sweep_id = wandb.sweep(sweep_config, project="lostpaw", entity="klotzandrei")
    wandb.agent(sweep_id, project="lostpaw", entity="klotzandrei")
