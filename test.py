import google.generativeai as genai

genai.configure(api_key="AQ.Ab8RN6IQqCMhdJYY_99ngv2KFCLc2yx6iDKULRMZ_oFwAG_Enw") 

print("Available Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)