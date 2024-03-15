### Pytorch ###

import torch

# info: str = f"""
# avaiable: {torch.cuda.is_available()}
# devices: {torch.cuda.device_count()}
# current:{torch.cuda.current_device()} : {torch.cuda.get_device_name()}
# """
# print(info)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if device.type == 'cuda':
    print(torch.cuda.get_device_name(0))
    print('Memory Usage:')
    print('Allocated:', round(torch.cuda.memory_allocated(0)/1024**3,1), 'GB')
    print('Cached:   ', round(torch.cuda.memory_reserved(0)/1024**3,1), 'GB')
else: 
    print('Current: ', device)