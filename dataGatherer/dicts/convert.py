import pickle
import os
import json

path = os.path.realpath(__file__)
dir = os.path.dirname(path)
# bt_id_file = 'bt_id.pickle'

# with open(bt_id_file, 'rb') as f:
#     bt_id = pickle.load(f)


# with open('bt_id.json', 'w') as fp:
#     json.dump(bt_id, fp)


bt_id_file = 'id_kp.pkl'

with open(bt_id_file, 'rb') as f:
    bt_id = pickle.load(f)


with open('id_kp.json', 'w') as fp:
    json.dump(bt_id, fp)