from rest_framework import serializers
from student.models import Student



class StudentSerializer (serializers.HyperlinkedModelSerializer) :

    class Meta :
        model = Student
        fields = ["id", "firstname", "lastname"]
