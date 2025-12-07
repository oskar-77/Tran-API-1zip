"""Document Processing Agent - Command Line Interface."""

import argparse
import sys
import json
from pathlib import Path
from src.agent import DocumentAgent


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║         Document Processing Agent v1.0                       ║
║         Extract • Convert • Transform                         ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary(agent: DocumentAgent):
    """Print document summary."""
    summary = agent.get_summary()
    
    print("\n📄 Document Summary:")
    print(f"   Title: {summary['title']}")
    print(f"   Source: {summary['source_filename']} ({summary['source_format']})")
    print(f"   Pages: {summary['page_count']}")
    print(f"   Total Blocks: {summary['total_blocks']}")
    print(f"   Images: {summary['image_count']}")
    print(f"   Tables: {summary['table_count']}")
    print(f"   Links: {summary['link_count']}")
    print(f"   Direction: {summary['direction']}")


def cmd_extract(args):
    """Handle extract command."""
    agent = DocumentAgent()
    
    try:
        print(f"\n📂 Loading: {args.input}")
        agent.load(args.input)
        print("✅ Document loaded successfully!")
        
        print_summary(agent)
        
        if args.output:
            output_path = args.output
        else:
            output_path = Path(args.input).stem + "_extracted.json"
        
        agent.export_to_json(output_path)
        print(f"\n💾 Saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def cmd_convert(args):
    """Handle convert command."""
    agent = DocumentAgent()
    
    try:
        print(f"\n📂 Loading: {args.input}")
        agent.load(args.input)
        print("✅ Document loaded successfully!")
        
        print_summary(agent)
        
        if args.output:
            output_path = args.output
        else:
            ext_map = {'html': '.html', 'docx': '.docx', 'markdown': '.md', 'md': '.md', 'json': '.json'}
            ext = ext_map.get(args.format, f'.{args.format}')
            output_path = Path(args.input).stem + f"_converted{ext}"
        
        print(f"\n🔄 Converting to {args.format}...")
        
        if args.format == 'json':
            agent.export_to_json(output_path)
        else:
            agent.export(args.format, output_path)
        
        print(f"✅ Conversion complete!")
        print(f"💾 Saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def cmd_info(args):
    """Handle info command."""
    agent = DocumentAgent()
    
    try:
        print(f"\n📂 Loading: {args.input}")
        agent.load(args.input)
        
        print_summary(agent)
        
        if args.metadata:
            print("\n📋 Metadata:")
            metadata = agent.get_metadata()
            for key, value in metadata.items():
                if value:
                    print(f"   {key}: {value}")
        
        if args.links:
            links = agent.get_links()
            if links:
                print(f"\n🔗 Links ({len(links)}):")
                for link in links[:20]:
                    print(f"   - {link.text}: {link.url}")
                if len(links) > 20:
                    print(f"   ... and {len(links) - 20} more")
        
        if args.tables:
            tables = agent.get_tables()
            if tables:
                print(f"\n📊 Tables ({len(tables)}):")
                for i, table in enumerate(tables[:5]):
                    print(f"   Table {i+1}: {table.row_count} rows x {table.column_count} columns")
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def cmd_formats(args):
    """Handle formats command."""
    print("\n📥 Supported Input Formats:")
    for fmt in DocumentAgent.get_supported_input_formats():
        print(f"   {fmt}")
    
    print("\n📤 Supported Output Formats:")
    for fmt in DocumentAgent.get_supported_output_formats():
        print(f"   {fmt}")


def cmd_demo(args):
    """Handle demo command - show a simple demonstration."""
    print("\n🎯 Document Processing Agent Demo")
    print("=" * 50)
    
    print("""
This agent can:

1. 📥 EXTRACT content from documents:
   - PDF files (.pdf)
   - Word documents (.docx)
   - PowerPoint presentations (.pptx)
   - Excel spreadsheets (.xlsx, .xlsm)
   - Text files (.txt)
   - Markdown files (.md)

2. 🔄 CONVERT to multiple formats:
   - HTML (with styles and embedded images)
   - Word DOCX (with formatting)
   - Markdown (with frontmatter)
   - JSON (structured data)

3. 📊 EXTRACT specific content:
   - Text with structure
   - Images with positions
   - Tables with cells
   - Links and URLs
   - Metadata

Example Usage:
--------------
# Extract and analyze a PDF
python main.py extract document.pdf

# Convert Word to HTML
python main.py convert report.docx -f html

# Get document info
python main.py info presentation.pptx --metadata --links

# Convert Excel to Markdown
python main.py convert data.xlsx -f markdown -o output.md
""")
    
    print("\nSupported formats:")
    cmd_formats(args)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Document Processing Agent - Extract and convert documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py extract document.pdf
  python main.py convert report.docx -f html -o report.html
  python main.py info presentation.pptx --metadata
  python main.py formats
  python main.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    extract_parser = subparsers.add_parser('extract', help='Extract content from document')
    extract_parser.add_argument('input', help='Input file path')
    extract_parser.add_argument('-o', '--output', help='Output JSON file path')
    extract_parser.set_defaults(func=cmd_extract)
    
    convert_parser = subparsers.add_parser('convert', help='Convert document to another format')
    convert_parser.add_argument('input', help='Input file path')
    convert_parser.add_argument('-f', '--format', required=True, 
                               choices=['html', 'docx', 'markdown', 'md', 'json'],
                               help='Output format')
    convert_parser.add_argument('-o', '--output', help='Output file path')
    convert_parser.set_defaults(func=cmd_convert)
    
    info_parser = subparsers.add_parser('info', help='Show document information')
    info_parser.add_argument('input', help='Input file path')
    info_parser.add_argument('--metadata', action='store_true', help='Show metadata')
    info_parser.add_argument('--links', action='store_true', help='Show links')
    info_parser.add_argument('--tables', action='store_true', help='Show tables info')
    info_parser.set_defaults(func=cmd_info)
    
    formats_parser = subparsers.add_parser('formats', help='Show supported formats')
    formats_parser.set_defaults(func=cmd_formats)
    
    demo_parser = subparsers.add_parser('demo', help='Show demonstration')
    demo_parser.set_defaults(func=cmd_demo)
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
