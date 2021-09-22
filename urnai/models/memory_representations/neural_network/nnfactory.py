from utils import constants
from utils.error import UnsuportedLibraryError
from utils.module_specialist import get_cls

class NeuralNetworkFactory():

    @classmethod
    def get_nn_model(action_size, state_size, build_model, lib=constants.Libraries.KERAS, gamma=0.99, learning_rate=0.001, seed_value=None, batch_size=32)
        if lib in constants.listoflibs:
            nn = None

            if lib == constants.Libraries.KERAS:
                #importing this way is safer because it uses importlib
                cls = get_cls("urnai.models.memory_representations.neural_network", "KerasDeepNeuralNetwork")
                nn = cls(action_size, state_size, build_model, gamma, learning_rate, seed_value, batch_size)
            if lib == constants.Libraries.PYTORCH:
                #importing this way is safer because it uses importlib
                cls = get_cls("urnai.models.memory_representations.neural_network", "PyTorchDeepNeuralNetwork")
                nn = PyTorchDeepNeuralNetwork(action_size, state_size, build_model, gamma, learning_rate, seed_value)

            return nn
        else:
            raise UnsuportedLibraryError(lib)