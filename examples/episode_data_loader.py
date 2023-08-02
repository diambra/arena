from diambra.arena.utils.diambra_data_loader import DiambraDataLoader
import argparse
import os

def main(dataset_path_input):
    if dataset_path_input is not None:
        dataset_path = dataset_path_input
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        dataset_path = os.path.join(base_path, "dataset")

    data_loader = DiambraDataLoader(dataset_path)

    n_loops = data_loader.reset()

    while n_loops == 0:
        observation, action, reward, done, info = data_loader.step()
        print("Observation: {}".format(observation))
        print("Action: {}".format(action))
        print("Reward: {}".format(reward))
        print("Done: {}".format(done))
        print("Info: {}".format(info))
        data_loader.render()

        if done:
            n_loops = data_loader.reset()

    # Return success
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type=str, default=None, help='Path to dataset')
    opt = parser.parse_args()
    print(opt)

    main(opt.dataset_path)
