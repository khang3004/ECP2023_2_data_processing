import os
import random
import pickle
from midi2remi import RemiPlus


def train_test_split(train_split, val_split):
    """Splits the dataset into training, validation, and test sets.

    Args:
        train_split (float): Proportion of data to be used for training.
        val_split (float): Proportion of data to be used for validation.
    """

    file_names = []  # List to hold the relative paths of readable files
    count = 0  # Counter for total number of files processed

    # Define directories
    data_dir = '../MusicData/Lakh_MIDI_Dataset/LMD_full/lmd_full'
    pkl_folder = '../data_processing/processed'

    # Traverse the directory containing MIDI files
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.mid'):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, data_dir)
                count += 1

                try:
                    # Process MIDI file with RemiPlus
                    data = RemiPlus(full_path, do_extract_chords=True, strict=True)
                    remi_events = data.get_remi_events()
                    description = data.get_description()

                    # Create folder structure for saving .pkl files
                    relative_folder = os.path.dirname(relative_path)
                    pkl_path = os.path.join(pkl_folder, relative_folder)
                    os.makedirs(pkl_path, exist_ok=True)

                    # # Remove .mid extension and save data as .pkl
                    file_name = os.path.splitext(file)[0]
                    pkl_file = os.path.join(pkl_path, f"{file_name}.pkl")
                    # with open(pkl_file, 'wb') as f:
                    #     pickle.dump({'events': remi_events, 'description': description}, f)
                    #
                    # print(f"Saved to {pkl_file}")
                    print(f"Read {pkl_file}")

                    # Append the relative path without .mid extension to the list
                    long_file_name = os.path.splitext(relative_path)[0]
                    file_names.append(long_file_name)

                except Exception as e:
                    print(f"Cannot read: {relative_path}. Error: {e}")

    print(f'Readable Files / Total Files: {len(file_names)}/{count}')

    # Shuffle and split the data
    random.shuffle(file_names)
    total_files = len(file_names)
    train_len = int(train_split * total_files)
    val_len = int(val_split * total_files)

    train_files = file_names[:train_len]
    val_files = file_names[train_len:train_len + val_len]

    # Save the split data as .pkl files
    with open(f'{pkl_folder}/train_split.pkl', 'wb') as f:
        pickle.dump(train_files, f)
    with open(f'{pkl_folder}/val_split.pkl', 'wb') as f:
        pickle.dump(val_files, f)

    if train_split + val_split != 1:
        test_files = file_names[train_len + val_len:]
        with open(f'{pkl_folder}/test_split.pkl', 'wb') as f:
            pickle.dump(test_files, f)
    else:
        print('No file left for Test set!')


if __name__ == '__main__':
    train_test_split(0.8, 0.1)
