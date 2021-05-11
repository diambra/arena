def make_diambra_imitationLearning_env(diambraIL, diambraIL_kwargs, seed=0,
                                       allow_early_resets=True):
    """
    Utility function for single proc env.

    :param diambraIL_kwargs: (dict) kwargs for Diambra IL env
    """

    assert diambraIL_kwargs["totalCpus"] == 1, "Only single proc environments can be created with this function, for a ready to use multiproc execution use the version based on StableBaselines"
    env = diambraIL(**diambraIL_kwargs, rank=0)

    return env
