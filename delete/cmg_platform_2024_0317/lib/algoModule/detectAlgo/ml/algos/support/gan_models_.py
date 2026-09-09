from tensorflow.keras.layers import Layer, Input, Dense, BatchNormalization, \
    Conv2DTranspose, Conv2D, LeakyReLU, ReLU, Reshape, Flatten
from tensorflow.keras.initializers import RandomNormal
from tensorflow.keras.regularizers import L2
from tensorflow.keras.models import Model

regularizer = L2(2.5e-5)
initializer = RandomNormal(stddev=0.02)

class DotLayer(Layer):
    def __init__(self, **kwargs):
        super(DotLayer, self).__init__()

    def build(self, input_shape):
        self.built = True

    def call(self, inputs, training=None):
        out = inputs[0]*inputs[1]
        return out

    def get_config(self):
        return super().get_config()

class BatchNorm(BatchNormalization):
    def call(self, inputs, training=None):
        return super(self.__class__, self).call(inputs, training=True)

def dense_block(units, input_layer, reshape_dim=None, prefix='', affix=''):
    dense = Dense(units,
                  kernel_regularizer=regularizer,
                  kernel_initializer=initializer,
                  name=prefix+"denseDense"+affix)(input_layer)
    bn = BatchNorm(name=prefix+"denseBN"+affix)(dense)
    if reshape_dim is not None:
        bn = Reshape(reshape_dim, name=prefix+"denseReshape"+affix)(bn)
    out = ReLU(name=prefix+"denseReLU"+affix)(bn)

    return out

def upconv_block(n_filter, filter_size, filter_stride, input_layer, bn=False, prefix='', affix=''):
    upconv = Conv2DTranspose(n_filter, filter_size,
                             strides=filter_stride,
                             kernel_initializer=initializer,
                             kernel_regularizer=regularizer,
                             padding='same',
                             name=prefix+"upconvConv2DTranspose"+affix)(input_layer)
    if bn:
        upconv = BatchNorm(name=prefix+"upconvBN"+affix)(upconv)
    out = ReLU(name=prefix+"upconvReLU"+affix)(upconv)

    return out


def conv_block(n_filter, filter_size, filter_stride, input_layer, prefix='', affix=''):
    conv = Conv2D(n_filter, filter_size,
                  strides=filter_stride,
                  kernel_initializer=initializer,
                  kernel_regularizer=regularizer,
                  padding='same',
                  name=prefix+'Conv'+affix)(input_layer)
    out = LeakyReLU(0.2, name=prefix+'ReLU'+affix)(conv)

    return out

def generator(in_sh=(4,), out_sh=(30,4), affix=''):
    input_concat = Input(shape=in_sh, name="Random_Input")
    dense1 = dense_block(256, input_concat, prefix="Gen_", affix="1")
    dense2 = dense_block(out_sh[0] * out_sh[1] * 128, dense1, reshape_dim=(out_sh[0], out_sh[1], 128), prefix="Gen_", affix="2")
    upconv = upconv_block(64, (4, 4), (1, 1), dense2, bn=True, prefix="Gen_", affix="1")
    out = Conv2DTranspose(1, (4, 4), (1, 1),
                          kernel_initializer=initializer,
                          kernel_regularizer=regularizer,
                          activation='tanh', padding='same',
                          name="Gen_Conv2DTranspose")(upconv)
    model = Model(inputs=input_concat, outputs=out, name="Generator"+affix)
    return model

def discriminator(in_sh=(30, 4, 1), affix=''):
    input_layer = Input(shape=in_sh, name='Feature_Input')
    input_layer1 = input_layer#BatchNorm()(input_layer)
    conv1 = conv_block(64, (4,4), (2,2), input_layer1, prefix="Feature_", affix="1")
    conv2 = conv_block(128, (4,4), (2,2), conv1, prefix="Feature_", affix="2")
    conv = BatchNorm(name="Feature_BN")(conv2)
    
    att1 = conv_block(64, (4,4), (2,2), input_layer, prefix="att_", affix="1")
    att2 = conv_block(128, (4,4), (2,2), att1, prefix="att_", affix="2")
    att = BatchNorm(name="att_BN")(att2)

    mixture = DotLayer(name="Feature_Attention_Mix")([conv, att])
    
    flat = Flatten(name="Arbit_Flatten")(mixture)
    dense = Dense(64,
                kernel_regularizer=regularizer,
                kernel_initializer=initializer,
                activation=LeakyReLU(0.2), 
                name="Arbit_Dense1")(flat)
    out = Dense(1,
                kernel_regularizer=regularizer,
                kernel_initializer=initializer,
                activation='sigmoid',
                name="Arbit_Dense2")(dense)

    model = Model(inputs=input_layer, outputs=out, name="Discriminator"+affix)

    return model

if __name__ == "__main__":
    d = discriminator((100,16,1))
    d.summary()
    g = generator((10,),(100,16))
    g.summary()
