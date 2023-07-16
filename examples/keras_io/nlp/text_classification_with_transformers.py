"""
Title: Text Classification with Transformers
Author: [Yash Srivastava](https://twitter.com/Yaaaaaashhh)
Date created: 2023/07/16
Last modified: 2023/07/16
Description: Implement a Transformer block as a Keras core layer and use it for text classification(Works on all backends).
Accelerator: GPU
"""
"""
## Setup
"""

import os
os.environ['KERAS_BACKEND'] = 'jax'   # Could be anything out of 'jax', 'torch' or 'tf'

import tensorflow as tf
import keras_core as keras

"""
## Implement a Transformer block as a layer
"""

class TransformerBlock(keras.layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super().__init__()
        self.att = keras.layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = keras.Sequential(
            [keras.layers.Dense(ff_dim, activation="relu"), keras.layers.Dense(embed_dim),]
        )
        self.layernorm1 = keras.layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = keras.layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = keras.layers.Dropout(rate)
        self.dropout2 = keras.layers.Dropout(rate)

    def build(self, input_shape):  # TODO: Check
      pass

    def call(self, inputs, training):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

"""
## Implement embedding layer

Two seperate embedding layers, one for tokens, one for token index (positions).
"""

class TokenAndPositionEmbedding(keras.layers.Layer):
    def __init__(self, maxlen, vocab_size, embed_dim):
        super().__init__()
        self.token_emb = keras.layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.pos_emb = keras.layers.Embedding(input_dim=maxlen, output_dim=embed_dim)

    def build(self, input_shape):    # TODO: Check.
        pass
        
    def call(self, x):
        maxlen = keras.ops.shape(x)[-1]    # keras.ops has built in numpy and other nn related functions.
        positions = tf.range(start=0, limit=maxlen, delta=1)   # TODO: Check if range is there or not.
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

"""
## Download and prepare the dataset
"""

vocab_size = 20000  # Only consider the top 20k words
maxlen = 200  # Only consider the first 200 words of each movie review
(x_train, y_train), (x_val, y_val) = keras.datasets.imdb.load_data(num_words=vocab_size)
print(len(x_train), "Training sequences")
print(len(x_val), "Validation sequences")
x_train = keras.utils.pad_sequences(x_train, maxlen=maxlen)
x_val = keras.utils.pad_sequences(x_val, maxlen=maxlen)

"""
## Create classifier model using transformer layer

Transformer layer outputs one vector for each time step of our input sequence. Here, we take the mean across all time steps and use a feed forward network on top of it to classify text.
"""
embed_dim = 32  # Embedding size for each token
num_heads = 2  # Number of attention heads
ff_dim = 32  # Hidden layer size in feed forward network inside transformer

inputs = keras.layers.Input(shape=(maxlen,))
embedding_layer = TokenAndPositionEmbedding(maxlen, vocab_size, embed_dim)
x = embedding_layer(inputs)
transformer_block = TransformerBlock(embed_dim, num_heads, ff_dim)
x = transformer_block(x, training=True)
x = keras.layers.GlobalAveragePooling1D()(x)
x = keras.layers.Dropout(0.1)(x)
x = keras.layers.Dense(20, activation="relu")(x)
x = keras.layers.Dropout(0.1)(x)
outputs = keras.layers.Dense(2, activation="softmax")(x)

model = keras.Model(inputs=inputs, outputs=outputs)

print(model)

"""
## Train and Evaluate
"""

model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
history = model.fit(
    x_train, y_train, batch_size=32, epochs=2, validation_data=(x_val, y_val)
)

loss, acc = history

print(f'Loss : {loss}, Accuracy : {acc}')