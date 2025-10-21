"""
Digital Garden Tools CLI
Main command-line interface for analyzing and maintaining your digital garden.
"""
import argparse
import logging
import sys
from pathlib import Path

from aqui_brain_dump.stats import generate_statistics, print_statistics_summary
from aqui_brain_dump.analyze_links import analyze_internal_links, print_link_analysis_summary
from aqui_brain_dump.check_external_links import check_external_links, print_external_links_summary


def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    log = logging.getLogger()
    log.setLevel(level)
    
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    log.addHandler(ch)
    
    # Also log to file
    log_dir = Path('stats')
    log_dir.mkdir(exist_ok=True, parents=True)
    fh = logging.FileHandler(log_dir / 'garden_tools.log', mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)


def cmd_stats(args):
    """Generate statistics about your digital garden"""
    print('\n🌱 Generating digital garden statistics...\n')
    stats = generate_statistics(
        output_file=args.output,
        parse_git=args.git
    )
    print_statistics_summary(stats)
    print(f'\n💾 Statistics saved to: {args.output}')


def cmd_links(args):
    """Analyze internal links"""
    print('\n🔗 Analyzing internal links...\n')
    analysis = analyze_internal_links(
        output_file=args.output,
        parse_git=args.git
    )
    print_link_analysis_summary(analysis)
    print(f'\n💾 Analysis saved to: {args.output}')


def cmd_external(args):
    """Check external links"""
    print('\n🌐 Checking external links...\n')
    print(f'⏱️  This may take a while (delay: {args.delay}s between requests)\n')
    results = check_external_links(
        output_file=args.output,
        parse_git=args.git,
        delay=args.delay,
        timeout=args.timeout
    )
    print_external_links_summary(results)
    print(f'\n💾 Results saved to: {args.output}')


def cmd_all(args):
    """Run all analyses"""
    print('\n🚀 Running all analyses...\n')
    
    # Statistics
    print('\n' + '='*60)
    print('1/3: GENERATING STATISTICS')
    print('='*60)
    stats = generate_statistics(
        output_file='stats/garden_stats.json',
        parse_git=args.git
    )
    print_statistics_summary(stats)
    
    # Internal links
    print('\n' + '='*60)
    print('2/3: ANALYZING INTERNAL LINKS')
    print('='*60)
    analysis = analyze_internal_links(
        output_file='stats/link_analysis.json',
        parse_git=args.git
    )
    print_link_analysis_summary(analysis)
    
    # External links
    print('\n' + '='*60)
    print('3/3: CHECKING EXTERNAL LINKS')
    print('='*60)
    print(f'⏱️  This may take a while...\n')
    results = check_external_links(
        output_file='stats/external_links.json',
        parse_git=args.git,
        delay=args.delay,
        timeout=args.timeout
    )
    print_external_links_summary(results)
    
    print('\n' + '='*60)
    print('✅ ALL ANALYSES COMPLETE')
    print('='*60)
    print('\n💾 All results saved to stats/ directory\n')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Digital Garden Tools - Analyze and maintain your digital garden',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate statistics
  python -m aqui_brain_dump.garden_tools stats
  
  # Analyze internal links
  python -m aqui_brain_dump.garden_tools links
  
  # Check external links
  python -m aqui_brain_dump.garden_tools external
  
  # Run all analyses
  python -m aqui_brain_dump.garden_tools all
  
  # Use git information for dates
  python -m aqui_brain_dump.garden_tools stats --git
  
  # Verbose output
  python -m aqui_brain_dump.garden_tools stats -v
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Generate statistics about your garden')
    stats_parser.add_argument('-o', '--output', default='stats/garden_stats.json',
                             help='Output file path (default: stats/garden_stats.json)')
    stats_parser.add_argument('--git', action='store_true',
                             help='Parse git information for accurate dates')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Links command
    links_parser = subparsers.add_parser('links', help='Analyze internal links')
    links_parser.add_argument('-o', '--output', default='stats/link_analysis.json',
                             help='Output file path (default: stats/link_analysis.json)')
    links_parser.add_argument('--git', action='store_true',
                             help='Parse git information')
    links_parser.set_defaults(func=cmd_links)
    
    # External links command
    external_parser = subparsers.add_parser('external', help='Check external HTTP/HTTPS links')
    external_parser.add_argument('-o', '--output', default='stats/external_links.json',
                                help='Output file path (default: stats/external_links.json)')
    external_parser.add_argument('--git', action='store_true',
                                help='Parse git information')
    external_parser.add_argument('-d', '--delay', type=float, default=0.5,
                                help='Delay between requests in seconds (default: 0.5)')
    external_parser.add_argument('-t', '--timeout', type=int, default=10,
                                help='Request timeout in seconds (default: 10)')
    external_parser.set_defaults(func=cmd_external)
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run all analyses')
    all_parser.add_argument('--git', action='store_true',
                           help='Parse git information')
    all_parser.add_argument('-d', '--delay', type=float, default=0.5,
                           help='Delay between requests for external links (default: 0.5)')
    all_parser.add_argument('-t', '--timeout', type=int, default=10,
                           help='Request timeout in seconds (default: 10)')
    all_parser.set_defaults(func=cmd_all)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(1)
    except Exception as e:
        logging.error(f'Error: {e}', exc_info=True)
        print(f'\n❌ Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

