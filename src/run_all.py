"""Regenerate every figure and table for the four business questions."""
import build_site
import q1_growth
import q2_concentration
import q3_sales_team
import q4_inventory
from load_data import load_tables


def main():
    """Load the workbook once and run Q1 to Q4 in order.

    Args:
        None.

    Returns:
        None. Each question writes its outputs to ``outputs/``.
    """
    tables = load_tables()
    q1_growth.main(tables)
    q2_concentration.main(tables)
    q3_sales_team.main(tables)
    q4_inventory.main(tables)
    build_site.main(tables)


if __name__ == "__main__":
    main()
