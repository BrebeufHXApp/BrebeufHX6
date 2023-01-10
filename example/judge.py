import tensorflow,numpy

class Judge(tensorflow.keras.models.Model):
    def __init__(self,**kwargs):
        super(Judge,self).__init__(**kwargs)
        self.textvectorization=tensorflow.keras.layers.TextVectorization(max_tokens=3000)
        self.embedding=tensorflow.keras.layers.Embedding(1000,64,mask_zero=True)
        self.rnn1=tensorflow.keras.layers.Bidirectional(tensorflow.keras.layers.LSTM(64,return_sequences=True))
        self.rnn2=tensorflow.keras.layers.Bidirectional(tensorflow.keras.layers.LSTM(32))
        self.fulllayer=tensorflow.keras.layers.Dense(64,activation="relu")
        self.dropout=tensorflow.keras.layers.Dropout(0.4)
        self.outputlayer=tensorflow.keras.layers.Dense(2,activation="softmax")
    
    def call(self,x):
        x=self.textvectorization(x)
        x=self.embedding(x)
        x=self.rnn1(x)
        x=self.rnn2(x)
        x=self.fulllayer(x)
        x=self.dropout(x)
        x=self.outputlayer(x)
        return x
    
def runjudge(judge,title,text):
    inputs=[[title+"\n"+text]]
    outputs=judge(inputs)
    result="accepted" if numpy.argmax(outputs)==0 else "rejected"
    if numpy.max(outputs)<0.7:result="unclear"
    return result

judge=tensorflow.keras.models.load_model("model")

if __name__=="__main__":
    texts=[]
    labels=[]
    for file in ["data/accepted.txt","data/rejected.txt"]:
        file=open(file,"rb")
        text=file.read().decode()
        file.close()
        for article in text.split("\r\n\r\n"):
            texts.append([article])
            labels.append(0 if file=="data/accepted.txt" else 1)

    judge=Judge()
    trainingdata=tensorflow.data.Dataset.from_tensor_slices((texts,labels)).shuffle(128).batch(2)
    judge.textvectorization.adapt(trainingdata.map(lambda text,label:text))
    loss=tensorflow.keras.losses.SparseCategoricalCrossentropy(from_logits=False)
    optimizer=tensorflow.keras.optimizers.Adam(learning_rate=0.001)
    judge.compile(loss=loss,optimizer=optimizer,metrics=["accuracy"])
    judge.fit(trainingdata,epochs=10)
    judge.save("model")