import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import tensorflow as tf
from tensorflow.python.framework import ops
from utils.error import IncoherentBuildModelError
from tensorflow.compat.v1 import Session,ConfigProto,placeholder,layers,train,global_variables_initializer
import numpy as np
import random
import os
import pickle
from .base.abmodel import LearningModel
from agents.actions.base.abwrapper import ActionWrapper
from agents.states.abstate import StateBuilder
from .model_builder.ModelBuilder import LAYER_INPUT, LAYER_FULLY_CONNECTED 

class DqlTfFlexible(LearningModel):

    #Some useful class constants
    DEFAULT_BUILD_MODEL = [ 
        {
            'type' : LAYER_INPUT,
            'shape' : [None, 10],
        },
        {
            'type' : LAYER_FULLY_CONNECTED,
            'nodes' : 50,
            'name' : 'fc1',
        },
        {
            'type' : LAYER_FULLY_CONNECTED,
            'nodes' : 50,
            'name' : 'fc2',
        },
        {
            'type' : LAYER_OUTPUT,
            'length' : 50, 
        },
    ]


    def __init__(self, action_wrapper: ActionWrapper, state_builder: StateBuilder, save_path='urnai/models/saved/', file_name='dqltfflexible', learning_rate=0.0002, gamma=0.95, name='DQN', build_model = DqlTfFlexible.DEFAULT_BUILD_MODEL):
        super(DqlTfFlexible, self).__init__(action_wrapper, state_builder, gamma, learning_rate, save_path, file_name, name)

        if save_path is None or file_name is None:
            raise TypeError

        # EXPLORATION PARAMETERS FOR EPSILON GREEDY STRATEGY
        self.explore_start = 1.0
        self.explore_stop = 0.01
        self.decay_rate = 0.0001
        self.decay_step = 0


        # ///// load_pickle should be called by the user! If it stays here, it may cause an accident if the user really wants a NEW OBJECT and at the same time he/she has a saved model inside the default folder, commenting this out!
        # Attempting to Load our serialized variables, as some of them will be used during the definition of our model
        #self.load_pickle()

        ops.reset_default_graph()
        tf.compat.v1.disable_eager_execution()

        # Initializing TensorFlow session
        self.sess = Session(config=ConfigProto(allow_soft_placement=True))

        # Defining the model's layers. Tensorflow's objects are stored into self.model_layers
        self.build_model = build_model
        self.make_model()

        self.pickle_obj = [self.decay_step, self.build_model]
        
        #Not being used anywhere, commenting out:
        #self.actions_ = placeholder(dtype=tf.float32, shape=[None, self.action_size], name='actions_')
        
        self.sess.run(global_variables_initializer())

        self.saver = train.Saver()
        # The default behavior of the __init__() method should be to create a new object, if the user wants to load from the default folder, he/she may call the load method.
        #self.load()

    def learn(self, s, a, r, s_, done, is_last_step: bool):
        qsa_values = self.sess.run(self.output_layer, feed_dict={self.inputs_: s})

        current_q = 0

        if done:
            current_q = r
        else:
            current_q = r + self.gamma * self.__maxq(s_)

        qsa_values[0, a] = current_q

        self.sess.run(self.optimizer, feed_dict={self.inputs_: s, self.tf_qsa: qsa_values})

        qsa_values = self.sess.run(self.output_layer, feed_dict={self.inputs_: s})

    def __maxq(self, state):
        values = self.sess.run(self.output_layer, feed_dict={self.inputs_: state})

        index = np.argmax(values[0])
        mxq = values[0, index]

        return mxq

    def choose_action(self, state, excluded_actions=[]):
        self.decay_step += 1

        expl_expt_tradeoff = np.random.rand()

        explore_probability = self.explore_stop + (self.explore_start - self.explore_stop) * np.exp(-self.decay_rate * self.decay_step)

        if explore_probability > expl_expt_tradeoff:
            random_action = random.choice(self.actions)

            # Removing excluded actions
            while random_action in excluded_actions:
                random_action = random.choice(self.actions)
            action = random_action
        else:
            action = self.predict(state, excluded_actions)

        return action

    def predict(self, state, excluded_actions=[]):
        q_values = self.sess.run(self.output_layer, feed_dict={self.inputs_: state})
        action_idx = np.argmax(q_values)

        # Removing excluded actions
        # This is possibly badly optimized, eventually look back into this
        while action_idx in excluded_actions:
            q_values = np.delete(q_values, action_idx)
            action_idx = np.argmax(q_values)
        
        action = self.actions[int(action_idx)]
        return action

    def get_full_persistance_pickle_path(self):
        return self.save_path + self.file_name + os.path.sep + "model_" + self.file_name + ".pkl"


    def get_full_persistance_tensorflow_path(self):
        return self.save_path + os.path.sep + "model_tensorflow_" + self.file_name

    def save(self):
        print("Saving model...")

        #Saving tensorflow stuff
        self.saver.save(self.sess, self.get_full_persistance_tensorflow_path())
        # Dumping (serializing) decay_step into a pickle file
        with open(self.get_full_persistance_pickle_path(), "wb") as pickle_out: 
            pickle.dump(self.pickle_obj, pickle_out)

    def load(self):
        #Load this model from persistant file
        #Tensorflow variables need to be loaded separated,
        #Because Session must be configured first. 
        self.load_pickle()
        self.make_model()
        self.load_tf()

    def load_tf(self)
        #Check if tf file exists
        exists = os.path.isfile(self.get_full_persistance_tensorflow_path + ".meta")
        #If yes, load it
        if exists:
            self.make_model()
            self.saver.restore(self.sess, self.save_path + self.file_name + "/" + self.file_name)
        else:
            #Else, raise exception
            raise FileNotFoundError(self.get_full_persistance_tensorflow_path + " was not found.")

    def load_pickle(self):
        #Check if pickle file exists
        exists_pickle = os.path.isfile(self.get_full_persistance_pickle_path)
        #If yes, load it
        if exists_pickle:
            with open(self.get_full_persistance_pickle_path(), "wb") as pickle_in: 
                self.pickle_obj = pickle.load(pickle_in)
                self.decay_step = self.pickle_obj[0]
                self.build_model = self.pickle_obj[1]
        else:
            #Else, raise exception
            raise FileNotFoundError(self.get_full_persistance_tensorflow_path + " was not found.")

    def make_model(self):
        #If the build model is the same as the default one, apply
        #the default properties to input and output
        if self.build_model == DqlTfFlexible.DEFAULT_BUILD_MODEL:
                    self.build_model[0]['shape'] = [None, self.state_size]
                    self.build_model[3]['length'] = self.actions_size

        #Load each layer
        self.model_layers = []
        for layer_model in self.build_model:
            if layer_model['type'] == LAYER_INPUT: 
                if self.build_model.index(layer_model) == 0:
                    self.model_layers.append(placeholder(dtype=tf.float32, 
                        shape=layer_model['shape'], name='inputs_'))
                else:
                    raise IncoherentBuildModelError("Input Layer must be the first one.") 
            elif layer_model['type'] == LAYER_FULLY_CONNECTED:
                self.model_layers.append(layers.dense(inputs=self.model_layers[-1], 
                    units=layer_model['nodes'], 
                    activation=tf.nn.relu, name=layer_model['name']))
            elif layer_model['type'] == LAYER_OUTPUT:
                self.model_layers.append(layers.dense(inputs=self.model_layers[-1], 
                    units=self.action_size,activation=None))

        #Setup output qsa layer and loss
        self.tf_qsa = placeholder(shape=[None, self.action_size], dtype=tf.float32)
        self.loss = tf.losses.mean_squared_error(self.tf_qsa, self.model_layers[-1])
        self.optimizer = train.AdamOptimizer(self.learning_rate).minimize(self.loss)

