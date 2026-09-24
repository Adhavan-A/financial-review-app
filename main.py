# main.py
from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import google.generativeai as genai
import json
from database import SessionLocal, Transaction, engine
from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import HTMLResponse 

# ---------------------------------------------------------

# ---------------------------------------------------------
genai.configure(api_key="AQ.Ab8RN6IQqCMhdJYY_99ngv2KFCLc2yx6iDKULRMZ_oFwAG_Enw")
model = genai.GenerativeModel('gemini-3.1-flash-lite')

app = FastAPI()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request bodies
class CategoryUpdate(BaseModel):
    category: str
    needs_review: bool = False

class ChatRequest(BaseModel):
    question: str

class VarianceRequest(BaseModel):
    current_month: str
    previous_month: str

# 1. Root Endpoint


@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/")
def read_root():
    return {"message": "Financial Review App is running! Go to /docs to test endpoints."}

# 2. Upload Endpoint (Requirement 1: Ingest Data)
@app.post("/upload")
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_excel(file.file)
    except Exception as e:
         return {"error": f"Error reading the Excel file: {e}"}
    
    records_added = 0
    for index, row in df.iterrows():
        existing = db.query(Transaction).filter(Transaction.id == str(row['Transaction ID'])).first()
        if not existing:
            new_tx = Transaction(
                id=str(row['Transaction ID']),
                date=row['Date'],
                description=str(row['Description']),
                counterparty=str(row['Counterparty']),
                amount=float(row['Amount']),
                method=str(row['Method'])
            )
            db.add(new_tx)
            records_added += 1
            
    db.commit()
    return {"message": f"Successfully ingested {records_added} transactions!"}

# 3. Get Transactions Endpoint
@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    return {"total": len(transactions), "transactions": transactions}

# 4. AI Categorize Endpoint 
@app.post("/categorize")
def categorize_transactions(db: Session = Depends(get_db)):
   
    uncategorized = db.query(Transaction).filter(Transaction.category == None).all()
    
    if not uncategorized:
        return {"message": "All transactions are already categorized!"}

    results = []
    for tx in uncategorized:
        prompt = f"""
        You are an expert AI accountant. Categorize the following transaction into one of these exact categories: 
        'Revenue', 'Cost of Goods Sold', 'Payroll', 'Operating Expenses', 'Other'.
        
        Transaction Description: {tx.description}
        Counterparty: {tx.counterparty}
        Amount: {tx.amount}
        
        Respond ONLY in valid JSON format like this:
        {{"category": "Operating Expenses", "needs_review": false}}
        
        If you are unsure or if the transaction is ambiguous, set "needs_review" to true.
        """
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.replace("```json", "").replace("```", "").strip()
            ai_data = json.loads(response_text)
            
            tx.category = ai_data.get("category", "Other")
            tx.needs_review = ai_data.get("needs_review", True)
            
            results.append({
                "id": tx.id, 
                "description": tx.description,
                "category": tx.category, 
                "needs_review": tx.needs_review
            })
            
        except Exception as e:
            print(f"Error categorizing {tx.id}: {e}")
            
    db.commit()
    return {"message": f"Categorized {len(results)} transactions", "results": results}

# 5. Manual Category Correction Endpoint 
@app.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: str, update_data: CategoryUpdate, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        return {"error": "Transaction not found"}
    
    tx.category = update_data.category
    tx.needs_review = update_data.needs_review
    db.commit()
    
    return {"message": "Transaction updated successfully", "id": tx.id, "category": tx.category}

# 6. Monthly P&L Calculation Endpoint 
@app.get("/pnl")
def calculate_pnl(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    
    pnl_by_month = {}
    
    for tx in transactions:
        if not tx.category:
            continue
            
        month_key = tx.date.strftime("%Y-%m")
        
        if month_key not in pnl_by_month:
            pnl_by_month[month_key] = {
                "Revenue": 0.0,
                "Cost of Goods Sold": 0.0,
                "Payroll": 0.0,
                "Operating Expenses": 0.0,
                "Other": 0.0
            }
            
        if tx.category in pnl_by_month[month_key]:
            pnl_by_month[month_key][tx.category] += tx.amount
        else:
            pnl_by_month[month_key]["Other"] += tx.amount

    final_pnl_report = {}
    for month, totals in pnl_by_month.items():
        revenue = totals.get("Revenue", 0.0)
        cogs = totals.get("Cost of Goods Sold", 0.0) 
        payroll = totals.get("Payroll", 0.0)
        opex = totals.get("Operating Expenses", 0.0)
        
        gross_profit = revenue + cogs
        operating_profit = gross_profit + payroll + opex
        
        final_pnl_report[month] = {
            "Revenue": round(revenue, 2),
            "Cost of Goods Sold": round(cogs, 2),
            "Gross Profit": round(gross_profit, 2),
            "Payroll": round(payroll, 2),
            "Operating Expenses": round(opex, 2),
            "Operating Profit": round(operating_profit, 2)
        }
        
    return {"monthly_pnl": final_pnl_report}

# 7. AI Financial Analyst Chatbot Endpoint 
@app.post("/chat")
def ai_financial_analyst(request: ChatRequest, db: Session = Depends(get_db)):
    pnl_data = calculate_pnl(db)
    
    system_prompt = f"""
    You are an AI Financial Analyst for NYC Restaurant Co.
    Use the following monthly P&L data to answer the user's question accurately.
    Do NOT invent numbers. If the data is not available to answer the question, say so.
    
    Financial Data Context:
    {json.dumps(pnl_data, indent=2)}
    
    User Question: {request.question}
    """
    
    try:
        response = model.generate_content(system_prompt)
        return {"question": request.question, "answer": response.text.strip()}
    except Exception as e:
        return {"error": f"Failed to get answer from AI: {e}"}

# 8. Variance Analysis Endpoint 
@app.post("/variance")
def analyze_variance(request: VarianceRequest, db: Session = Depends(get_db)):
    # P&L Data edukurom
    pnl_data = calculate_pnl(db).get("monthly_pnl", {})
    
    if request.current_month not in pnl_data or request.previous_month not in pnl_data:
        return {"error": "Data for one or both requested months is missing. Make sure transactions are categorized."}
        
    current = pnl_data[request.current_month]
    previous = pnl_data[request.previous_month]
    
    variances = {}
    for key in current.keys():
        variances[key] = round(current[key] - previous.get(key, 0.0), 2)
        
    system_prompt = f"""
    You are an expert AI Financial Analyst for NYC Restaurant Co.
    Analyze the financial variance between {request.previous_month} and {request.current_month}.
    
    Previous Month ({request.previous_month}): {json.dumps(previous)}
    Current Month ({request.current_month}): {json.dumps(current)}
    Calculated Variances (Current - Previous): {json.dumps(variances)}
    
    Identify the most material changes (biggest increases or decreases in revenue or expenses) 
    and explain what drove the change. Keep it professional, concise, and highlight specific numbers.
    """
    
    try:
        response = model.generate_content(system_prompt)
        return {
            "current_month": request.current_month,
            "previous_month": request.previous_month,
            "numerical_variances": variances,
            "ai_explanation": response.text.strip()
        }
    except Exception as e:
        return {"error": f"Failed to get variance explanation from AI: {e}"}