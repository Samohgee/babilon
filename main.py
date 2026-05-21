from kivy.app inport App
from kivy.uix.label import label

   class BabilonApp(App):
       def build(self):
           return Label(text="Babilon AI is working!")


BabilonApp().run()
