import argparse
import yaml
import re


def _parse_args(parser, config_parser):
    # Do we have a config file to parse?
    args_config, remaining = config_parser.parse_known_args()

    # Split arguments with a dot into two seperate arguments like this:
    # "--foo.bar=abc" => "--foo" "bar=abc"
    remaining = [
        a
        for arg in remaining
        for a in re.sub(
            r"--([A-Za-z0.9_-]+)\.([A-Za-z0.9_-]+)=", r"--\1#~f#\2=", arg
        ).split("#~f#")
    ]

    if args_config.config:
        with open(args_config.config, "r") as f:
            cfg = yaml.safe_load(f)
            parser.set_defaults(**cfg)

    # The main arg parser parses the rest of the args, the usual
    # defaults will have been overridden if config file specified.
    args = parser.parse_args(remaining)

    return args


def get_args():
    # The first arg parser parses out only the --config argument, this argument is used to
    # load a yaml file containing key-values that override the defaults for the main parser below
    config_parser = argparse.ArgumentParser(
        description="Training Configuration", add_help=False
    )
    config_parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="FILE",
        default="",
        help="Path to the YAML config file specifying the default parameters.",
    )

    parser = argparse.ArgumentParser(description="PyTorch implementation of TODO")

    # Data and Model locations
    parser.add_argument(
        "--info_path",
        type=str,
        help="Path to the data information file",
    )

    parser.add_argument(
        "--similarity_probability",
        type=float,
        default=0.5,
        help="Probability of a pair being similar",
    )

    parser.add_argument(
        "--batches_per_epoch",
        type=int,
        default=128,
        help="Number of batches per epoch",
    )

    parser.add_argument(
        "--cross_validiton_k_fold",
        type=int,
        default=1,
        help="Number of cross validation folds, each fold will be an individual run",
    )

    parser.add_argument(
        "--model_path",
        type=str,
        help="Path to the model file",
    )

    # Model parameters
    parser.add_argument(
        "--latent_space_size",
        type=int,
        help="""Output dimension of the model. 
        Represents the latent space size""",
    )

    parser.add_argument(
        "--contrastive_margin",
        type=float,
        help="Margin (temperature?) for the contrastive loss",
    )

    parser.add_argument(
        "--contrastive_epsilon",
        type=float,
        help="Value to add to the euclidean distance to improve numerical stability",
    )

    # Training parameters
    parser.add_argument(
        "--epochs",
        type=int,
        help="Number of epochs to train for",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size",
    )

    parser.add_argument(
        "--test_batch_size",
        type=int,
        help="The batch size for testing.",
    )


    parser.add_argument(
        "--test_batch_count",
        type=int,
        help="Number of batches for testing.",
    )

    parser.add_argument(
        "--save_model_every",
        type=int,
        help="The model will be saved ever N epochs.",
    )

    parser.add_argument(
        "--early_stopping_epochs",
        type=int,
        help="How many epochs without improving accuracy before we stop.",
    )

    # Otpimizer parameters
    parser.add_argument(
        "--optimizer",
        type=str,
        help="Optimizer to use: Adam, AdamW, or SGD",
    )

    parser.add_argument(
        "--optimizer_params",
        type=str,  # User adds list of strings, and we parse them later
        nargs="+",
        action="extend",
        help="""Optimizer settings: lr, betas, weight_decay, dampening,
        momentum, eps, amsgrad, nesterov.
        Example: --optimizer_params lr=0.001""",
    )

    # Logging
    parser.add_argument(
        "--run_name",
        type=str,
        help="""Display name to use in wandb. 
        Also used for the path to save the model. 
        Provide a unique name, or give the same 
        name to continue training.""",
    )
    parser.add_argument(
        "--use_wandb",
        nargs="?",
        action="store",
        default=True,
        help="Whether to save output on wandb.",
    )
    parser.add_argument(
        "--use_tqdm",
        nargs="?",
        action="store",
        default=True,
        help="Whether to use tqdm for progress bar.",
    )

    args = _parse_args(parser, config_parser)

    if args.run_name is None:
        import time

        args.run_name = "{}".format(time.strftime("%Y_%m_%d_%H%M%S"))

    # Convert optimizer params to dict
    if type(args.optimizer_params) is list:
        args.optimizer_params = dict(
            [tuple(param.split("=")) for param in args.optimizer_params]
        )

        # Convert values to float
        for key, value in args.optimizer_params.items():
            value = str(value)
            if key in ["amsgrad", "nesterov"]:
                args.optimizer_params[key] = value.lower() == "true"
            elif value.startswith("("):
                args.optimizer_params[key] = [
                    float(v.strip()) for v in value.strip("()").split(",")
                ]
            else:
                args.optimizer_params[key] = float(value)

    return args
