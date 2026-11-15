from datetime import date, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.db_context import customer_scope


def financial_snapshot(db: Session, customer_id: str):
    customer_scope(db, customer_id)
    p = db.execute(text("SELECT colchon_meses, cuota_ingreso, nivel_deuda FROM app.perfil WHERE customer_id=:cid"), {"cid": customer_id}).mappings().one()
    a = db.execute(text("SELECT monthly_income,monthly_expenses,current_savings,monthly_debt_payment,income_stability FROM app.onboarding_financiero WHERE customer_id=:cid"), {"cid": customer_id}).mappings().first()
    if a:
        income, expenses, savings, debt = (Decimal(a[k]) for k in ('monthly_income','monthly_expenses','current_savings','monthly_debt_payment'))
        cushion = savings / expenses if expenses > 0 else Decimal('0')
        ratio = debt / income if income > 0 else Decimal('0')
        return {'income':income,'expenses':expenses,'savings':savings,'debt':debt,'cushion':cushion,'ratio':ratio,'source':'onboarding'}
    tx = db.execute(text("""SELECT tipo, COALESCE(SUM(monto),0) AS total FROM app.transacciones
        WHERE customer_id=:cid AND moneda='PEN' AND fecha_hora >= now()-interval '90 days'
        GROUP BY tipo"""), {'cid':customer_id}).mappings().all()
    mv = db.execute(text("""SELECT tipo, COALESCE(SUM(monto),0) AS total FROM app.movimientos_usuario
        WHERE customer_id=:cid AND fecha BETWEEN current_date-90 AND current_date
        GROUP BY tipo"""), {'cid':customer_id}).mappings().all()
    totals={'ingreso':Decimal('0'),'gasto':Decimal('0')}
    for row in [*tx,*mv]: totals[row['tipo']]+=Decimal(row['total'])
    if not any(totals.values()):
        raise HTTPException(status_code=503,detail='No hay onboarding ni historial financiero suficiente para calcular indicadores')
    return {'income':totals['ingreso']/3,'expenses':totals['gasto']/3,'savings':Decimal('0'),'debt':Decimal('0'),'cushion':Decimal(p['colchon_meses']),'ratio':Decimal(p['cuota_ingreso'] or 0),'source':'movimientos_90_dias'}


def balance_projection(s, horizon):
    # Proyección lineal determinista; NO es un modelo predictivo entrenado.
    net=(s['income']-s['expenses']-s['debt'])/Decimal('30')
    start=s['savings']
    return [round(float(start+net*day),2) for day in range(1,horizon+1)]
