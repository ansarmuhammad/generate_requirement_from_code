"""
Pricing Calculator with Business Rules
Processes customer orders with various discount and rate calculations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys


class PricingCalculator:
    """Calculate pricing with various discount rules and region loading"""
    
    # Product rates - These should be configured based on your actual products
    # You can modify these rates or load them from a separate configuration file
    PRODUCT_RATES = {
        'product_a': {'individual': 100.0, 'corporate': 90.0},
        'product_b': {'individual': 150.0, 'corporate': 135.0},
        'product_c': {'individual': 200.0, 'corporate': 180.0},
        'product_d': {'individual': 75.0, 'corporate': 67.5},
        'product_e': {'individual': 250.0, 'corporate': 225.0},
        # Default rates for unknown products
        'default': {'individual': 100.0, 'corporate': 85.0}
    }
    
    def __init__(self):
        """Initialize the pricing calculator"""
        self.df = None
        
    def load_csv(self, filepath):
        """Load CSV file and validate required columns"""
        try:
            self.df = pd.read_csv(filepath)
            print(f"Loaded {len(self.df)} rows from {filepath}")
            
            # Validate required columns
            required_cols = ['Customer', 'Product', 'Season', 'Volume', 'Region', 'Status']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
                
            # Clean and standardize data
            self.df['Customer'] = self.df['Customer'].str.lower().str.strip()
            self.df['Product'] = self.df['Product'].str.lower().str.strip()
            self.df['Season'] = self.df['Season'].str.lower().str.strip()
            self.df['Region'] = self.df['Region'].str.upper().str.strip()
            self.df['Status'] = self.df['Status'].str.lower().str.strip()
            self.df['Volume'] = pd.to_numeric(self.df['Volume'], errors='coerce').fillna(0).astype(int)
            
            return True
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def calculate_rule_a_discount(self, season):
        """Rule A: Spring season has a 5% discount"""
        if season == 'spring':
            return 5.0
        return 0.0
    
    def calculate_rule_b_volume_discount(self, volume):
        """Rule B: Volume-based discounts
        - Volume < 100: 0% discount
        - Volume < 1000: 5% discount  
        - Volume >= 1000: 10% discount
        """
        if volume < 100:
            return 0.0
        elif volume < 1000:
            return 5.0
        else:
            return 10.0
    
    def calculate_rule_c_category_discount(self, customer):
        """Rule C: Strategic customer gets 5% discount"""
        if customer == 'strategic':
            return 5.0
        return 0.0
    
    def get_product_rates(self, product, status):
        """Rule D: Get individual or corporate rate for product"""
        # Get product rates, use default if product not found
        product_key = product if product in self.PRODUCT_RATES else 'default'
        rates = self.PRODUCT_RATES[product_key]
        
        if status == 'corporate':
            return rates['corporate'], 0, rates['corporate']
        else:
            return rates['individual'], rates['individual'], 0
    
    def calculate_rule_e_region_loading(self, region, receivable_after_discount):
        """Rule E: EMEA is charged 10% extra on the Receivable after discount"""
        if region == 'EMEA':
            return receivable_after_discount * 0.10
        return 0.0
    
    def process_calculations(self):
        """Process all calculations according to business rules"""
        if self.df is None:
            print("No data loaded. Please load CSV first.")
            return
        
        # Initialize calculated columns
        self.df['Discount'] = 0.0
        self.df['Volume discount'] = 0.0
        self.df['Category discount'] = 0.0
        self.df['Individual rate'] = 0.0
        self.df['Corporate rate'] = 0.0
        self.df['Receivable before discount'] = 0.0
        self.df['Total discounts'] = 0.0
        self.df['Receivable after discount'] = 0.0
        self.df['Region loading'] = 0.0
        self.df['Total receivables'] = 0.0
        self.df['Comments'] = ''
        
        # Process each row
        for idx, row in self.df.iterrows():
            # Rule A: Season discount
            season_discount = self.calculate_rule_a_discount(row['Season'])
            self.df.at[idx, 'Discount'] = season_discount
            
            # Rule B: Volume discount
            volume_discount = self.calculate_rule_b_volume_discount(row['Volume'])
            self.df.at[idx, 'Volume discount'] = volume_discount
            
            # Rule C: Category discount
            category_discount = self.calculate_rule_c_category_discount(row['Customer'])
            self.df.at[idx, 'Category discount'] = category_discount
            
            # Rule D: Product rates
            rate, individual_rate, corporate_rate = self.get_product_rates(
                row['Product'], row['Status']
            )
            self.df.at[idx, 'Individual rate'] = individual_rate
            self.df.at[idx, 'Corporate rate'] = corporate_rate
            
            # Calculate receivable before discount
            receivable_before = row['Volume'] * rate
            self.df.at[idx, 'Receivable before discount'] = receivable_before
            
            # Calculate total discounts (compound discounts)
            # All discounts applied on the original receivable before discount
            total_discount_rate = season_discount + volume_discount + category_discount
            discount_amount = receivable_before * (total_discount_rate / 100)

            self.df.at[idx, 'Total discounts'] = discount_amount
            
            # Calculate receivable after discount
            receivable_after = receivable_before - discount_amount
            self.df.at[idx, 'Receivable after discount'] = receivable_after
            
            # Rule E: Region loading
            region_loading = self.calculate_rule_e_region_loading(
                row['Region'], receivable_after
            )
            self.df.at[idx, 'Region loading'] = region_loading
            
            # Calculate total receivables
            total_receivables = receivable_after + region_loading
            self.df.at[idx, 'Total receivables'] = total_receivables
            
            # Generate comments
            comments = []
            if season_discount > 0:
                comments.append(f"Spring discount: {season_discount}%")
            if volume_discount > 0:
                comments.append(f"Volume discount: {volume_discount}%")
            if category_discount > 0:
                comments.append(f"Strategic discount: {category_discount}%")
            if region_loading > 0:
                comments.append(f"EMEA loading: 10%")
            
            self.df.at[idx, 'Comments'] = "; ".join(comments) if comments else "Standard pricing"
        
        # Round all numeric columns to 2 decimal places
        numeric_cols = ['Discount', 'Volume discount', 'Category discount', 
                       'Individual rate', 'Corporate rate', 'Receivable before discount',
                       'Total discounts', 'Receivable after discount', 'Region loading',
                       'Total receivables']
        
        for col in numeric_cols:
            self.df[col] = self.df[col].round(2)
        
        print("Calculations completed successfully!")
    
    def save_output(self, output_filepath=None):
        """Save processed data to CSV"""
        if self.df is None:
            print("No data to save.")
            return
        
        if output_filepath is None:
            # Generate default output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = f"pricing_output_{timestamp}.csv"
        
        self.df.to_csv(output_filepath, index=False)
        print(f"Output saved to: {output_filepath}")
        
        # Display summary statistics
        self.print_summary()
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Total records processed: {len(self.df)}")
        print(f"Total volume: {self.df['Volume'].sum():,.0f}")
        print(f"Total receivables before discount: ${self.df['Receivable before discount'].sum():,.2f}")
        print(f"Total discounts applied: ${self.df['Total discounts'].sum():,.2f}")
        print(f"Total receivables after discount: ${self.df['Receivable after discount'].sum():,.2f}")
        print(f"Total region loading: ${self.df['Region loading'].sum():,.2f}")
        print(f"Final total receivables: ${self.df['Total receivables'].sum():,.2f}")
        print("="*60)
        
        # Group by summaries
        print("\nBy Customer Type:")
        customer_summary = self.df.groupby('Customer')['Total receivables'].sum()
        for customer, total in customer_summary.items():
            print(f"  {customer.capitalize()}: ${total:,.2f}")
        
        print("\nBy Region:")
        region_summary = self.df.groupby('Region')['Total receivables'].sum()
        for region, total in region_summary.items():
            print(f"  {region}: ${total:,.2f}")
        
        print("\nBy Season:")
        season_summary = self.df.groupby('Season')['Total receivables'].sum()
        for season, total in season_summary.items():
            print(f"  {season.capitalize()}: ${total:,.2f}")


def main():
    """Main execution function"""
    print("Pricing Calculator with Business Rules")
    print("="*60)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Prompt for input file
        input_file = input("Enter the path to your input CSV file: ").strip()
        if not input_file:
            print("No input file provided. Exiting.")
            return
        
        output_file = input("Enter output file path (press Enter for auto-generated name): ").strip()
        output_file = output_file if output_file else None
    
    # Process the file
    calculator = PricingCalculator()
    
    if calculator.load_csv(input_file):
        calculator.process_calculations()
        calculator.save_output(output_file)
    else:
        print("Failed to process the file. Please check your input.")


if __name__ == "__main__":
    main()