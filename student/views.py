from django.shortcuts import render
from student.models import Student
from django.http import HttpResponse, JsonResponse
from student.serializers import StudentSerializer
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
from django.http import HttpResponse
import json
@csrf_exempt
@api_view(['POST'])
def addstudent(request):
    if request.method == "POST":
        data = request.data
        print("Data received: ", data)

    seril = StudentSerializer(data)
    print(seril)
    new_student = Student(firstname="", lastname="Fu")
    if new_student.firstname == "" :
        return HttpResponse("ERROR: A new student should have a firstname")
    else :
        new_student.save()
        students = Student.objects.all()

        return JsonResponse({"Message": "The new student have been added..",
                        "data": StudentSerializer(students, many=True).data}, safe=False)

    return HttpResponse("You have requested to add student...")

@api_view(['GET', 'POST'])
def deletestudent(request, id):
    data = request.data
    print("Data received: ", id)

    students = Student.objects.all()
    student_to_delete = Student.objects.filter(id=int(id))

    if len(student_to_delete) > 0 :
        print("Student to delete: ",student_to_delete)
        student_to_delete = student_to_delete[0]
        student_to_delete.delete()

    else:
        return HttpResponse(f"ERROR: the student {id} do not exist")
    return JsonResponse({"Message": "The student has been deleted..",
                        "data": StudentSerializer(students, many=True).data}, safe=False)
def getstudents(request):
    students = Student.objects.all()

    return JsonResponse({"Message": "All the students have been retreived.",
                        "data": StudentSerializer(students, many=True).data}, safe=False)
