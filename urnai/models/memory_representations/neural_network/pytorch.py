from .abneuralnetwork import ABNeuralNetwork
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

class PyTorchDeepNeuralNetwork(ABNeuralNetwork):
    """
    Implementation of a Generic Deep Neural Network using PyTorch

    This class inherits from ABNeuralNetwork, so it already has all abstract methods
    necessary for learning, predicting outputs, and building a model. All that this
    class does is implement those abstract methods, and implement the methods necessary
    for adding Neural Network layers, such as add_input_layer(), add_output_layer(),
    add_fully_connected_layer().

    Differently from KerasDeepNeuralNetwork, this class is not able to dynamically build
    Neural Network architectures that use convolutional layers, due to the complexity 
    of PyTorch's initialization of convolutional layers and a general difficulty in 
    fitting that complexity to URNAI's achitecture. To use PyTorch with convolutional 
    layers, one has to inherit from this class and manually create your model, we recommend
    you do that in self.make_model().

    This class also implements the methodes necessary for saving and loading the model
    from local memory.

    Parameters:
        action_output_size: int
            size of our output
        state_input_shape: tuple
            shape of our input
        build_model: Python dict
            A dict representing the NN's layers. Can be generated by the 
            ModelBuilder.get_model_layout() method from an instantiated ModelBuilder object.
        gamma: Float
            Gamma parameter for the Deep Q Learning algorithm
        alpha: Float
            This is the Learning Rate of the model
        seed: Integer (default None)
            Value to assing to random number generators in Python and our ML libraries to try 
            and create reproducible experiments
        batch_size: Integer
            Size of our learning batch to be passed to the Machine Learning library
    """

    def __init__(self, action_output_size, state_input_shape, build_model, gamma, alpha, seed = None, batch_size=32):       
        
        # device needs to be set before calling the parent's constructor
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        super().__init__(action_output_size, state_input_shape, build_model, gamma, alpha, seed, batch_size)

        # Optimizer needs to be set after super call because we define self.model inside it
        self.optimizer = optim.Adam(self.model.model_layers.parameters(), lr=self.alpha)
        

    def add_input_layer(self, idx):
        self.model.model_layers.append(nn.Linear(self.state_input_shape, self.build_model[idx]['nodes']).to(self.device))

    def add_output_layer(self, idx):
        self.model.model_layers.append(nn.Linear(self.build_model[idx-1]['nodes'], self.action_output_size).to(self.device))

    def add_fully_connected_layer(self, idx):
        self.model.model_layers.append(nn.Linear(self.build_model[idx-1]['nodes'], self.build_model[idx]['nodes']).to(self.device))

    def update(self, state, target_output):
        # transform our state from numpy array to pytorch tensor and then feed it to our model (model)
        # the result of this is our expected output
        torch_state = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
        expected_output = self.model(torch_state)

        # transform our target output from numpy array to pytorch tensor
        target_output = torch.from_numpy(target_output).float().unsqueeze(0).to(self.device)

        # calculate loss using expected_output and target_output
        loss = torch.nn.MSELoss()(expected_output, target_output).to(self.device)

        # using loss to update the neural network (doing an optmizer step)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def get_output(self, state):
        # convert numpy format to something that pytorch understands
        state = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
        # put the network into evaluation mode
        self.model.eval()
        # get network output
        with torch.no_grad():
            action_values = self.model(state)
        # put the network back to training mode again
        self.model.train()
        # return the output
        output = np.squeeze(action_values.cpu().data.numpy())
        return output

    def set_seed(self, seed):
        if seed != None:
            torch.manual_seed(self.seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        return seed

    def create_base_model(self):
        model = self.SubDeepQNetwork()
        return model

    def copy_model_weights(self, model_to_copy):
        self.model.load_state_dict(model_to_copy.state_dict())

    class SubDeepQNetwork(nn.Module):
        def __init__(self):
            super().__init__()
            self.model_layers = nn.ModuleList()

        def forward(self,x):
            for i in range(len(self.model_layers) - 1):
                layer = self.model_layers[i]
                x = F.relu(self.model_layers[i](x))
            return self.model_layers[-1](x)