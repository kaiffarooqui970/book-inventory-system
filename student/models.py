from django.db import models

# Create your models here.
class Student(models.Model):
  id = models.BigAutoField(primary_key=True)
  firstname = models.CharField(max_length=255)
  lastname = models.CharField(max_length=255)


  def order_by(arg):
      pass
  # def __init__(self, firstname, lastname):
  #     self.firstname = firstname
  #     self.lastname = lastname
