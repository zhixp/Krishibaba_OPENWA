"""
Export script for AI training data
Extracts voice notes, chat logs, and user facts for model training
"""
import asyncio
import aiosqlite
import json
import csv
from pathlib import Path
from datetime import datetime

DB_PATH = "d:/BUILDS_TOOLS/Krishi baba App/backend/krishi_baba.db"
OUTPUT_DIR = "d:/BUILDS_TOOLS/Krishi baba App/backend/training_data"

async def export_voice_dataset():
    """Export voice notes with transcriptions for speech model training"""
    print("📢 Exporting voice dataset...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT user_id, file_path, transcription, file_size, created_at
            FROM voice_logs
            WHERE transcription IS NOT NULL
            ORDER BY created_at DESC
        """)
        rows = await cursor.fetchall()
        
        # Save as CSV
        output_file = Path(OUTPUT_DIR) / f"voice_dataset_{datetime.now().strftime('%Y%m%d')}.csv"
        output_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'audio_file', 'transcription', 'file_size', 'timestamp'])
            writer.writerows(rows)
        
        print(f"✅ Exported {len(rows)} voice samples to {output_file}")


async def export_chat_dataset():
    """Export Q&A pairs for conversational AI training"""
    print("💬 Exporting chat dataset...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get user-assistant pairs
        cursor = await db.execute("""
            SELECT 
                m1.uid,
                m1.content as user_message,
                m2.content as assistant_response,
                m1.timestamp
            FROM chat_messages m1
            JOIN chat_messages m2 
                ON m1.uid = m2.uid 
                AND m2.timestamp > m1.timestamp
                AND m2.role = 'assistant'
            WHERE m1.role = 'user'
            ORDER BY m1.timestamp DESC
        """)
        rows = await cursor.fetchall()
        
        # Save as JSON for easy import
        dataset = []
        for row in rows:
            dataset.append({
                "user_id": row[0],
                "input": row[1],
                "output": row[2],
                "timestamp": row[3]
            })
        
        output_file = Path(OUTPUT_DIR) / f"chat_dataset_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(dataset)} Q&A pairs to {output_file}")


async def export_user_insights():
    """Export aggregated user facts for analysis"""
    print("📊 Exporting user insights...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Aggregate facts by type
        cursor = await db.execute("""
            SELECT 
                fact_type,
                fact_value,
                COUNT(*) as frequency,
                AVG(confidence) as avg_confidence
            FROM user_facts
            GROUP BY fact_type, fact_value
            ORDER BY frequency DESC
        """)
        rows = await cursor.fetchall()
        
        insights = {}
        for row in rows:
            fact_type = row[0]
            if fact_type not in insights:
                insights[fact_type] = []
            
            insights[fact_type].append({
                "value": row[1],
                "frequency": row[2],
                "confidence": round(row[3], 2)
            })
        
        output_file = Path(OUTPUT_DIR) / f"user_insights_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported insights to {output_file}")


async def main():
    print("=" * 50)
    print("🚀 Krishi Baba - Training Data Export")
    print("=" * 50)
    
    await export_voice_dataset()
    await export_chat_dataset()
    await export_user_insights()
    
    print("\n✅ All exports complete!")
    print(f"📁 Check: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
