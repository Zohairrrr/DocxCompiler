import os
import json
from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .services import AIWordEngine

# 1. Browser View (Web UI homepage)
def docx_compiler_view(request):
    if request.method == "POST":
        prompt = request.POST.get("prompt")
        if not prompt:
            return HttpResponse("no good prompt", status=400)
        
        try:
            file_path = AIWordEngine.generate_math_document(prompt)
            response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename="math.docx")
            return response
        except Exception as e:
            return HttpResponse(f"Compilation Engine Failure: {str(e)}", status=500)
            
    return render(request, "docx_compiler/index.html")
@csrf_exempt  
def compile_api_view(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed", status=405)
        
    prompt = None
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt")
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON Payload.", status=400)
    else:
        prompt = request.POST.get("prompt")
            
    if not prompt:
        return HttpResponse("Missing 'prompt' parameter in request.", status=400)
        
    try:
        file_path = AIWordEngine.generate_math_document(prompt)
        with open(file_path, 'rb') as docx_file:
            response = HttpResponse(
                docx_file.read(), 
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            response['Content-Disposition'] = 'attachment; filename="AI_Compiled_Math.docx"'
            return response
            
    except Exception as e:
        return HttpResponse(f"Internal Compilation Error: {str(e)}", status=500)