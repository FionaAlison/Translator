import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
from numpy import transpose
from image_recognition import Net
from os.path import join

cwd: str = '/'.join(__file__.split("/")[:-2])

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
transform = transforms.Compose( [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))] )
testset = torchvision.datasets.CIFAR10(root=join(cwd, 'data'), train=False, download=False, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=1, shuffle=True, num_workers=4)

# Load the model
PATH = join(cwd, 'models', 'cifar_net.pth')
net = Net()
net.load_state_dict(torch.load(PATH))

# Sample test
def imshow(img):
    img = img / 2 + 0.5
    npimg = img.numpy()
    plt.imshow(transpose(npimg, (1, 2, 0)))
    plt.show()

dataiter = iter(testloader)
images, labels = next(dataiter)

print(f'{'Actual:':15s} {classes[labels[0]]:5s}')

outputs = net(images)
_, predicted = torch.max(outputs, 1)
print(f'{'Predicted:':15s} {classes[predicted[0]]:5s}')

imshow(torchvision.utils.make_grid(images))