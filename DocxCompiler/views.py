import os
from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from .services import AIWordEngine

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