"""Manage pharmacy inventory, prescriptions, and stock reports."""
import ast
import hashlib
import json
import operator
import os
import secrets
from datetime import date, datetime

medicines = {}
DB_PASSWORD = os.getenv("PHARMACY_PASSWORD", "")

# Only these arithmetic operators are allowed in dosage formulas.
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def add_medicine(name, qty=0, price=0.0,
                 expiry="2099-12-31", audit=None):
    """Add medicine stock and record the stock operation."""
    if not isinstance(name, str) or not name:
        raise ValueError("Medicine name must be a non-empty string.")
    if qty < 0 or price < 0:
        raise ValueError("Quantity and price cannot be negative.")

    if name not in medicines:
        medicines[name] = {"qty": 0, "price": price, "expiry": expiry}

    medicines[name]["qty"] += qty
    if audit is None:
        audit = []
    audit.append(
        f"{datetime.now()}: Stocked {qty} units of {name}"
    )
    return audit


def dispense_medicine(name, qty):
    """Dispense medicine if sufficient stock is available."""
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("Quantity must be a positive integer.")
    if name not in medicines:
        raise KeyError(f"Medicine not found: {name}")
    if medicines[name]["qty"] < qty:
        raise ValueError("Insufficient stock.")

    medicines[name]["qty"] -= qty
    if medicines[name]["qty"] == 0:
        del medicines[name]


def get_quantity(name):
    """Return the available quantity of a medicine."""
    return medicines[name]["qty"]


def is_expired(name):
    """Check whether a medicine has expired."""
    expiry = datetime.strptime(
        medicines[name]["expiry"], "%Y-%m-%d"
    ).date()
    return expiry < date.today()


def bill_amount(prescription):
    """Calculate the total cost of a prescription."""
    total = 0
    for item_name, quantity in prescription:
        total += medicines[item_name]["price"] * quantity
    return total


def _evaluate_formula_node(node):
    """Evaluate only approved arithmetic nodes."""
    if isinstance(node, ast.Expression):
        return _evaluate_formula_node(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _evaluate_formula_node(node.left)
        right = _evaluate_formula_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is too large.")
        result = _ALLOWED_OPERATORS[type(node.op)](left, right)
        if not isinstance(result, (int, float)) or abs(result) > 1e12:
            raise ValueError("Formula result is outside the allowed range.")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _evaluate_formula_node(node.operand)
        )
    raise ValueError("Formula contains an unsupported operation.")


def calculate_dosage(formula):
    """Calculate a dosage from a restricted arithmetic expression."""
    try:
        tree = ast.parse(formula, mode="eval")
        result = _evaluate_formula_node(tree)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("Invalid dosage formula.") from error
    if not isinstance(result, (int, float)):
        raise ValueError("Dosage must be numeric.")
    return result


def patient_id(name, phone):
    """Return a SHA-256 digest for the supplied patient details."""
    return hashlib.sha256((name + phone).encode("utf-8")).hexdigest()


def generate_rx_number():
    """Generate an unpredictable prescription reference."""
    return f"RX-{secrets.randbelow(900000) + 100000}"


def save_stock(file="pharmacy.json"):
    """Save medicine inventory as JSON."""
    with open(file, "w", encoding="utf-8") as stock_file:
        json.dump(medicines, stock_file, indent=4)


def load_stock(file="pharmacy.json"):
    """Load medicine inventory from a JSON file."""
    with open(file, "r", encoding="utf-8") as stock_file:
        loaded_medicines = json.load(stock_file)

    if not isinstance(loaded_medicines, dict):
        raise ValueError("Invalid stock file format.")

    medicines.clear()
    medicines.update(loaded_medicines)


def print_label(name):
    """Print a medicine dispensing label."""
    print(f"Dispensing label: {name}")


def expiring_soon(days=30):
    """Return medicines expiring within the specified number of days."""
    result = []
    for name, medicine in medicines.items():
        expiry = datetime.strptime(
            medicine["expiry"], "%Y-%m-%d"
        ).date()
        remaining_days = (expiry - date.today()).days
        if 0 <= remaining_days < days:
            result.append(name)
    return result


def pharmacist_login(password):
    """Check a password against the configured pharmacy password."""
    return bool(DB_PASSWORD) and secrets.compare_digest(
        password, DB_PASSWORD
    )


def print_stock():
    """Print the current pharmacy inventory."""
    print("===== Pharmacy Stock Report =====")
    for name, medicine in medicines.items():
        print(
            f"{name} -> {medicine['qty']} units, "
            f"Rs. {medicine['price']}, exp {medicine['expiry']}"
        )


def main():
    """Run the pharmacy manager demonstration."""
    add_medicine("Paracetamol 500mg", 200, 1.5, "2027-06-30")
    add_medicine("Amoxicillin 250mg", 40, 6.0, "2027-12-15")
    add_medicine("Cetirizine 10mg", 10, 2.0, "2027-03-31")
    dispense_medicine("Paracetamol 500mg", 30)

    print("Paracetamol stock:", get_quantity("Paracetamol 500mg"))
    print("Amoxicillin expired?", is_expired("Amoxicillin 250mg"))
    print(
        "Bill:",
        bill_amount([
            ("Paracetamol 500mg", 10),
            ("Amoxicillin 250mg", 5),
        ]),
    )
    print("Dosage (mg/day):", calculate_dosage("250 * 2"))
    print("Patient ID:", patient_id("Asha", "9876543210"))
    print("Rx number:", generate_rx_number())
    print("Login:", pharmacist_login(DB_PASSWORD) if DB_PASSWORD else False)
    print_label("Paracetamol 500mg")
    print_stock()


if __name__ == "__main__":
    main()
