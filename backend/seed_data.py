"""
Sample Data Seed Script
Populates database with test data for development
"""
import asyncio
import aiosqlite
from datetime import datetime, timedelta
import random

DB_PATH = "./krishi_baba.db"


async def seed_mandi_prices():
    """Add sample mandi price data"""
    print("🌾 Seeding mandi prices...")
    
    crops = [
        "गेहूं (Wheat)", "धान (Paddy)", "सोयाबीन (Soybean)",
        "कपास (Cotton)", "मक्का (Maize)", "चना (Gram)",
        "अरहर (Pigeon Pea)", "मूंगफली (Groundnut)"
    ]
    
    locations = [
        ("भोपाल (Bhopal)", "Madhya Pradesh", "Bhopal"),
        ("इंदौर (Indore)", "Madhya Pradesh", "Indore"),
        ("विदिशा (Vidisha)", "Madhya Pradesh", "Vidisha"),
        ("रायसेन (Raisen)", "Madhya Pradesh", "Raisen"),
        ("सीहोर (Sehore)", "Madhya Pradesh", "Sehore"),
    ]
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Clear existing data
        await db.execute("DELETE FROM mandi_prices")
        
        # Add sample prices for last 7 days
        today = datetime.now()
        inserted = 0
        
        for days_ago in range(7):
            date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            for crop in crops:
                for location, state, district in locations:
                    # Generate random prices
                    base_price = random.randint(2000, 6000)
                    modal_price = base_price
                    min_price = base_price - random.randint(100, 500)
                    max_price = base_price + random.randint(100, 500)
                    
                    await db.execute(
                        """INSERT INTO mandi_prices 
                           (crop_name, mandi_location, modal_price, min_price, max_price,
                            date_scraped, state, district)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (crop, location, modal_price, min_price, max_price,
                         date, state, district)
                    )
                    inserted += 1
        
        await db.commit()
        print(f"  ✅ Inserted {inserted} mandi price records")


async def seed_govt_schemes():
    """Add sample government schemes"""
    print("📜 Seeding government schemes...")
    
    schemes = [
        {
            "name": "PM-KISAN (प्रधानमंत्री किसान सम्मान निधि)",
            "benefit": "₹6000 प्रति वर्ष तीन किस्तों में सीधे बैंक खाते में",
            "eligibility": "सभी छोटे और सीमांत किसान जिनके पास 2 हेक्टेयर तक जमीन है",
            "url": "https://pmkisan.gov.in",
            "category": "Subsidy",
            "state": "Central"
        },
        {
            "name": "फसल बीमा योजना (PMFBY)",
            "benefit": "प्राकृतिक आपदा से फसल नुकसान पर बीमा कवर",
            "eligibility": "सभी किसान जो खरीफ/रबी फसल उगाते हैं",
            "url": "https://pmfby.gov.in",
            "category": "Insurance",
            "state": "Central"
        },
        {
            "name": "किसान क्रेडिट कार्ड (KCC)",
            "benefit": "कम ब्याज दर पर 3 लाख तक का कृषि ऋण",
            "eligibility": "सभी किसान जो नियमित खेती करते हैं",
            "url": "https://www.nabard.org",
            "category": "Loan",
            "state": "Central"
        },
        {
            "name": "मुख्यमंत्री कृषक दुर्घटना कल्याण योजना",
            "benefit": "खेती के दौरान दुर्घटना में ₹2 लाख तक सहायता",
            "eligibility": "मध्य प्रदेश के सभी किसान",
            "url": "https://mpkrishi.mp.gov.in",
            "category": "Insurance",
            "state": "Madhya Pradesh"
        },
        {
            "name": "भावांतर भुगतान योजना",
            "benefit": "बाजार मूल्य और MSP के अंतर का भुगतान",
            "eligibility": "मध्य प्रदेश के पंजीकृत किसान",
            "url": "https://mpkrishi.mp.gov.in",
            "category": "Subsidy",
            "state": "Madhya Pradesh"
        }
    ]
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Clear existing data
        await db.execute("DELETE FROM govt_schemes")
        
        for scheme in schemes:
            await db.execute(
                """INSERT INTO govt_schemes 
                   (scheme_name, benefit_summary, eligibility, source_url, category, state)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (scheme['name'], scheme['benefit'], scheme['eligibility'],
                 scheme['url'], scheme['category'], scheme['state'])
            )
        
        await db.commit()
        print(f"  ✅ Inserted {len(schemes)} government schemes")


async def seed_test_users():
    """Add test users"""
    print("👥 Seeding test users...")
    
    users = [
        {
            "uid": "test_user_1",
            "name": "रमेश कुमार",
            "phone": "9876543210",
            "pincode": "462001",
            "district": "Bhopal"
        },
        {
            "uid": "test_user_2",
            "name": "सुरेश पाटील",
            "phone": "9876543211",
            "pincode": "464001",
            "district": "Vidisha"
        }
    ]
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Clear existing test users
        await db.execute("DELETE FROM users WHERE uid LIKE 'test_%'")
        
        for user in users:
            await db.execute(
                """INSERT INTO users (uid, name, phone, default_pincode, default_district)
                   VALUES (?, ?, ?, ?, ?)""",
                (user['uid'], user['name'], user['phone'], user['pincode'], user['district'])
            )
        
        await db.commit()
        print(f"  ✅ Inserted {len(users)} test users")


async def main():
    print("=" * 60)
    print("🚜 KRISHI BABA - Seeding Sample Data")
    print("=" * 60)
    print()
    
    await seed_mandi_prices()
    await seed_govt_schemes()
    await seed_test_users()
    
    print()
    print("=" * 60)
    print("✅ Sample data seeded successfully!")
    print("=" * 60)
    print()
    print("You can now test the API with:")
    print("  Test User ID: test_user_1")
    print("  Sample queries:")
    print("    - 'Bhopal ka gehun ka bhav kya hai?'")
    print("    - 'Aaj ka mausam kaisa hai?'")
    print("    - 'Kya koi sarkar ki yojana hai?'")
    print()


if __name__ == "__main__":
    asyncio.run(main())
