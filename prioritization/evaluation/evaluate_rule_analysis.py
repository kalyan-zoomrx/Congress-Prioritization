import json

from typing import Dict, List, Any, Set
from collections import Counter
from datetime import datetime
from prioritization.utils.logger import get_logger

logger = get_logger("RuleAnalysisEvaluator")


class RuleAnalysisEvaluator:
    """
    Comprehensive evaluator for parsed rule analysis output.
    Compares parsed output against input files to validate correctness.
    """
    
    def __init__(
        self,
        rules_file: str,
        client_keywords_file: str,
        parsed_rules: Dict[str, Any],
        custom_synonyms_file: str = None
    ):
        """
        Initialize evaluator with input files and parsed output.
        
        Args:
            rules_file: Path to rules.csv
            client_keywords_file: Path to client_keywords.csv
            parsed_rules: Parsed rules dictionary (or path to JSON)
            custom_synonyms_file: Optional path to custom_synonyms.csv
        """
        self.rules_file = rules_file
        self.client_keywords_file = client_keywords_file
        self.custom_synonyms_file = custom_synonyms_file
        
        # Load parsed rules
        if isinstance(parsed_rules, str):
            with open(parsed_rules, 'r', encoding='utf-8') as f:
                self.parsed_rules = json.load(f)
        else:
            self.parsed_rules = parsed_rules
        
        # Load input data
        self.input_rules = self._load_rules_csv()
        self.input_keywords = self._load_keywords_csv()
        self.input_synonyms = self._load_synonyms_csv() if custom_synonyms_file else {}
        
        self.metrics = {}
        
        logger.info("Initialized RuleAnalysisEvaluator")
    
    # ============================================================================
    # INPUT FILE LOADING
    # ============================================================================
    
    def _load_rules_csv(self) -> List[str]:
        """Load rules from CSV file."""
        rules = []
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split by newlines and filter empty lines
                rules = [line.strip() for line in content.split('\n') if line.strip()]
            logger.info(f"Loaded {len(rules)} rules from {self.rules_file}")
        except Exception as e:
            logger.error(f"Error loading rules CSV: {e}")
        return rules
    
    def _load_keywords_csv(self) -> Set[str]:
        """Load client keywords from CSV file."""
        keywords = set()
        try:
            with open(self.client_keywords_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split by commas and newlines, clean up
                for line in content.split('\n'):
                    for kw in line.split(','):
                        cleaned = kw.strip()
                        if cleaned:
                            keywords.add(cleaned)
            logger.info(f"Loaded {len(keywords)} keywords from {self.client_keywords_file}")
        except Exception as e:
            logger.error(f"Error loading keywords CSV: {e}")
        return keywords
    
    def _load_synonyms_csv(self) -> Dict[str, List[str]]:
        """Load custom synonyms from CSV file."""
        synonyms = {}
        try:
            with open(self.custom_synonyms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Assuming format: keyword, synonym1, synonym2, ...
                    keyword = row.get('keyword', '').strip()
                    if keyword:
                        synonyms[keyword] = [v.strip() for v in row.values() if v.strip() and v.strip() != keyword]
            logger.info(f"Loaded {len(synonyms)} synonym mappings from {self.custom_synonyms_file}")
        except Exception as e:
            logger.error(f"Error loading synonyms CSV: {e}")
        return synonyms
    
    # ============================================================================
    # MAIN EVALUATION
    # ============================================================================
    
    def evaluate_all(self) -> Dict[str, Any]:
        """
        Run all evaluation metrics and return comprehensive report.
        
        Returns:
            Dictionary containing all evaluation metrics
        """
        logger.info("Starting comprehensive evaluation")
        
        self.metrics['syntactic'] = self.evaluate_syntactic()
        self.metrics['semantic'] = self.evaluate_semantic()
        self.metrics['input_alignment'] = self.evaluate_input_alignment()
        
        self.metrics['overall_score'] = self._calculate_overall_score()
        self.metrics['timestamp'] = datetime.now().isoformat()
        self.metrics['issues'] = self._collect_issues()
        self.metrics['recommendations'] = self._generate_recommendations()
        
        logger.info(f"Evaluation complete. Overall score: {self.metrics['overall_score']:.1f}/100")
        
        return self.metrics
    
    # ============================================================================
    # SYNTACTIC EVALUATION
    # ============================================================================
    
    def evaluate_syntactic(self) -> Dict[str, Any]:
        """Evaluate syntactic correctness of parsed output."""
        logger.info("Running syntactic evaluation")
        
        syntactic_metrics = {
            'schema_validation': self._validate_schema(),
            'completeness': self._check_completeness(),
            'format_consistency': self._check_format_consistency(),
            'data_quality': self._check_data_quality()
        }
        
        syntactic_metrics['syntactic_score'] = self._calculate_syntactic_score(syntactic_metrics)
        
        return syntactic_metrics
    
    def _validate_schema(self) -> Dict[str, Any]:
        """Step 1.1: Validate JSON schema structure."""
        schema_metrics = {
            'has_relevance_rule': False,
            'has_priority_rules': False,
            'relevance_rule_valid': False,
            'priority_rules_valid': False,
            'schema_compliance_score': 0.0,
            'issues': []
        }
        
        required_fields = {
            'relevance_rule': ['rule_text', 'approach', 'key_concepts', 'reasoning'],
            'priority_rule': ['priority', 'rule_text', 'approach', 'key_concepts', 'reasoning']
        }
        
        # Check relevance rule
        if 'relevance_rule' in self.parsed_rules:
            schema_metrics['has_relevance_rule'] = True
            rel_rule = self.parsed_rules['relevance_rule']
            
            missing_fields = [f for f in required_fields['relevance_rule'] if f not in rel_rule]
            if missing_fields:
                schema_metrics['issues'].append(f"Relevance rule missing fields: {missing_fields}")
            else:
                schema_metrics['relevance_rule_valid'] = True
        else:
            schema_metrics['issues'].append("Missing 'relevance_rule' in output")
        
        # Check priority rules
        if 'priority_rules' in self.parsed_rules:
            schema_metrics['has_priority_rules'] = True
            priority_rules = self.parsed_rules['priority_rules']
            
            if isinstance(priority_rules, list) and len(priority_rules) > 0:
                valid_rules = 0
                for i, rule in enumerate(priority_rules):
                    missing_fields = [f for f in required_fields['priority_rule'] if f not in rule]
                    if missing_fields:
                        schema_metrics['issues'].append(f"Priority rule {i} missing fields: {missing_fields}")
                    else:
                        valid_rules += 1
                
                schema_metrics['priority_rules_valid'] = valid_rules == len(priority_rules)
                schema_metrics['valid_priority_rules_count'] = valid_rules
                schema_metrics['total_priority_rules_count'] = len(priority_rules)
            else:
                schema_metrics['issues'].append("Priority rules is not a valid list")
        else:
            schema_metrics['issues'].append("Missing 'priority_rules' in output")
        
        # Calculate overall schema compliance
        compliance_checks = [
            schema_metrics['has_relevance_rule'],
            schema_metrics['has_priority_rules'],
            schema_metrics['relevance_rule_valid'],
            schema_metrics['priority_rules_valid']
        ]
        schema_metrics['schema_compliance_score'] = (sum(compliance_checks) / len(compliance_checks)) * 100
        
        return schema_metrics
    
    def _check_completeness(self) -> Dict[str, Any]:
        """Step 1.2: Check completeness of parsed output."""
        completeness_metrics = {
            'priority_levels_present': [],
            'expected_priority_levels': ['High', 'Medium', 'Low'],
            'missing_priority_levels': [],
            'keywords_count': 0,
            'categories_count': 0,
            'has_exclusions': False,
            'exclusions_count': 0,
            'completeness_score': 0.0,
            'issues': []
        }
        
        # Check priority levels
        if 'priority_rules' in self.parsed_rules:
            priorities = [rule.get('priority') for rule in self.parsed_rules['priority_rules']]
            completeness_metrics['priority_levels_present'] = priorities
            
            expected = set(completeness_metrics['expected_priority_levels'])
            present = set(priorities)
            completeness_metrics['missing_priority_levels'] = list(expected - present)
            
            if completeness_metrics['missing_priority_levels']:
                completeness_metrics['issues'].append(
                    f"Missing priority levels: {completeness_metrics['missing_priority_levels']}"
                )
        
        # Count keywords across all rules
        all_keywords = set()
        all_categories = set()
        total_exclusions = 0
        
        # Relevance rule
        if 'relevance_rule' in self.parsed_rules:
            rel_concepts = self.parsed_rules['relevance_rule'].get('key_concepts', {})
            rel_keywords = rel_concepts.get('keywords', [])
            all_keywords.update(rel_keywords)
            all_categories.update(rel_concepts.get('categories', []))
            
            if not rel_keywords:
                completeness_metrics['issues'].append("Relevance rule has no keywords")
        
        # Priority rules
        if 'priority_rules' in self.parsed_rules:
            for i, rule in enumerate(self.parsed_rules['priority_rules']):
                concepts = rule.get('key_concepts', {})
                keywords = concepts.get('keywords', [])
                all_keywords.update(keywords)
                all_categories.update(concepts.get('categories', []))
                
                if not keywords:
                    completeness_metrics['issues'].append(f"Priority rule {i} ({rule.get('priority')}) has no keywords")
                
                exclusions = rule.get('exclusions', [])
                if exclusions:
                    total_exclusions += len(exclusions)
        
        completeness_metrics['keywords_count'] = len(all_keywords)
        completeness_metrics['categories_count'] = len(all_categories)
        completeness_metrics['has_exclusions'] = total_exclusions > 0
        completeness_metrics['exclusions_count'] = total_exclusions
        
        # Calculate completeness score
        checks = [
            len(completeness_metrics['missing_priority_levels']) == 0,
            completeness_metrics['keywords_count'] > 0,
            completeness_metrics['categories_count'] > 0,
            completeness_metrics['has_exclusions']
        ]
        completeness_metrics['completeness_score'] = (sum(checks) / len(checks)) * 100
        
        return completeness_metrics
    
    def _check_format_consistency(self) -> Dict[str, Any]:
        """Step 1.3: Check formatting consistency across rules."""
        format_metrics = {
            'duplicate_keywords': [],
            'duplicate_count': 0,
            'empty_fields': [],
            'empty_fields_count': 0,
            'whitespace_issues': [],
            'format_consistency_score': 0.0,
            'issues': []
        }
        
        # Collect all keywords
        all_keywords = []
        
        if 'relevance_rule' in self.parsed_rules:
            rel_keywords = self.parsed_rules['relevance_rule'].get('key_concepts', {}).get('keywords', [])
            all_keywords.extend(rel_keywords)
        
        if 'priority_rules' in self.parsed_rules:
            for rule in self.parsed_rules['priority_rules']:
                keywords = rule.get('key_concepts', {}).get('keywords', [])
                all_keywords.extend(keywords)
        
        # Find duplicates
        keyword_counts = Counter(all_keywords)
        duplicates = {kw: count for kw, count in keyword_counts.items() if count > 1}
        format_metrics['duplicate_keywords'] = list(duplicates.keys())
        format_metrics['duplicate_count'] = len(duplicates)
        
        if format_metrics['duplicate_count'] > 0:
            format_metrics['issues'].append(
                f"Found {format_metrics['duplicate_count']} duplicate keywords across rules"
            )
        
        # Check for empty fields
        empty_fields = []
        
        if 'relevance_rule' in self.parsed_rules:
            rel_rule = self.parsed_rules['relevance_rule']
            if not rel_rule.get('key_concepts', {}).get('keywords', []):
                empty_fields.append('relevance_rule.key_concepts.keywords')
            if not rel_rule.get('reasoning', '').strip():
                empty_fields.append('relevance_rule.reasoning')
        
        if 'priority_rules' in self.parsed_rules:
            for i, rule in enumerate(self.parsed_rules['priority_rules']):
                if not rule.get('key_concepts', {}).get('keywords', []):
                    empty_fields.append(f'priority_rules[{i}].key_concepts.keywords')
                if not rule.get('reasoning', '').strip():
                    empty_fields.append(f'priority_rules[{i}].reasoning')
        
        format_metrics['empty_fields'] = empty_fields
        format_metrics['empty_fields_count'] = len(empty_fields)
        
        # Check for whitespace issues
        whitespace_issues = []
        for kw in all_keywords:
            if kw != kw.strip():
                whitespace_issues.append(kw)
        
        format_metrics['whitespace_issues'] = whitespace_issues
        
        # Calculate format consistency score
        total_keywords = len(all_keywords)
        duplicate_penalty = (format_metrics['duplicate_count'] / total_keywords * 100) if total_keywords > 0 else 0
        empty_penalty = format_metrics['empty_fields_count'] * 10
        whitespace_penalty = len(whitespace_issues) * 2
        
        format_metrics['format_consistency_score'] = max(0, 100 - duplicate_penalty - empty_penalty - whitespace_penalty)
        
        return format_metrics
    
    def _check_data_quality(self) -> Dict[str, Any]:
        """Step 1.4: Check data quality metrics."""
        quality_metrics = {
            'keyword_length_stats': {},
            'reasoning_length_stats': {},
            'category_distribution': {},
            'suspicious_keywords': [],
            'data_quality_score': 0.0,
            'issues': []
        }
        
        # Collect data
        keyword_lengths = []
        reasoning_lengths = []
        category_counts = Counter()
        all_keywords = []
        
        if 'relevance_rule' in self.parsed_rules:
            rel_rule = self.parsed_rules['relevance_rule']
            keywords = rel_rule.get('key_concepts', {}).get('keywords', [])
            all_keywords.extend(keywords)
            keyword_lengths.extend([len(kw) for kw in keywords])
            reasoning_lengths.append(len(rel_rule.get('reasoning', '')))
            
            categories = rel_rule.get('key_concepts', {}).get('categories', [])
            category_counts.update(categories)
        
        if 'priority_rules' in self.parsed_rules:
            for rule in self.parsed_rules['priority_rules']:
                keywords = rule.get('key_concepts', {}).get('keywords', [])
                all_keywords.extend(keywords)
                keyword_lengths.extend([len(kw) for kw in keywords])
                reasoning_lengths.append(len(rule.get('reasoning', '')))
                
                categories = rule.get('key_concepts', {}).get('categories', [])
                category_counts.update(categories)
        
        # Calculate statistics
        if keyword_lengths:
            quality_metrics['keyword_length_stats'] = {
                'min': min(keyword_lengths),
                'max': max(keyword_lengths),
                'avg': sum(keyword_lengths) / len(keyword_lengths),
                'total_keywords': len(keyword_lengths)
            }
            
            # Check for suspicious keywords
            suspicious = [kw for kw in all_keywords if len(kw) < 2 or len(kw) > 100]
            quality_metrics['suspicious_keywords'] = suspicious
            if suspicious:
                quality_metrics['issues'].append(
                    f"Found {len(suspicious)} keywords with unusual length"
                )
        
        if reasoning_lengths:
            quality_metrics['reasoning_length_stats'] = {
                'min': min(reasoning_lengths),
                'max': max(reasoning_lengths),
                'avg': sum(reasoning_lengths) / len(reasoning_lengths)
            }
        
        quality_metrics['category_distribution'] = dict(category_counts)
        
        # Quality score
        quality_checks = []
        
        if keyword_lengths:
            reasonable_keywords = sum(1 for length in keyword_lengths if 2 <= length <= 100)
            quality_checks.append(reasonable_keywords / len(keyword_lengths))
        
        if reasoning_lengths:
            substantial_reasoning = sum(1 for length in reasoning_lengths if length > 20)
            quality_checks.append(substantial_reasoning / len(reasoning_lengths))
        
        quality_metrics['data_quality_score'] = (sum(quality_checks) / len(quality_checks) * 100) if quality_checks else 0
        
        return quality_metrics
    
    def _calculate_syntactic_score(self, syntactic_metrics: Dict[str, Any]) -> float:
        """Calculate overall syntactic score."""
        scores = [
            syntactic_metrics['schema_validation']['schema_compliance_score'],
            syntactic_metrics['completeness']['completeness_score'],
            syntactic_metrics['format_consistency']['format_consistency_score'],
            syntactic_metrics['data_quality']['data_quality_score']
        ]
        return sum(scores) / len(scores)
    
    # ============================================================================
    # SEMANTIC EVALUATION
    # ============================================================================
    
    def evaluate_semantic(self) -> Dict[str, Any]:
        """Evaluate semantic correctness of parsed output."""
        logger.info("Running semantic evaluation")
        
        semantic_metrics = {
            'rule_logic': self._validate_rule_logic(),
            'keyword_semantics': self._validate_keyword_semantics(),
            'exclusion_analysis': self._analyze_exclusions(),
            'reasoning_quality': self._evaluate_reasoning_quality()
        }
        
        semantic_metrics['semantic_score'] = self._calculate_semantic_score(semantic_metrics)
        
        return semantic_metrics
    
    def _validate_rule_logic(self) -> Dict[str, Any]:
        """Step 2.1: Validate logical consistency of rules."""
        logic_metrics = {
            'mutual_exclusivity_score': 100.0,
            'priority_hierarchy_valid': True,
            'overlapping_keywords': [],
            'overlap_percentage': 0.0,
            'logic_score': 0.0,
            'issues': []
        }
        
        if 'priority_rules' not in self.parsed_rules:
            logic_metrics['issues'].append("No priority rules found")
            return logic_metrics
        
        priority_rules = self.parsed_rules['priority_rules']
        
        # Check priority hierarchy
        expected_order = ['High', 'Medium', 'Low']
        actual_order = [rule.get('priority') for rule in priority_rules]
        logic_metrics['priority_hierarchy_valid'] = actual_order == expected_order
        
        if not logic_metrics['priority_hierarchy_valid']:
            logic_metrics['issues'].append(
                f"Priority order incorrect. Expected {expected_order}, got {actual_order}"
            )
        
        # Check for keyword overlaps
        keyword_sets = {}
        
        for rule in priority_rules:
            priority = rule.get('priority')
            keywords = set(rule.get('key_concepts', {}).get('keywords', []))
            keyword_sets[priority] = keywords
        
        # Calculate overlaps
        overlaps = []
        priorities = list(keyword_sets.keys())
        
        for i, p1 in enumerate(priorities):
            for p2 in priorities[i+1:]:
                overlap = keyword_sets[p1] & keyword_sets[p2]
                if overlap:
                    overlaps.append({
                        'priorities': [p1, p2],
                        'overlapping_keywords': list(overlap)[:10],
                        'count': len(overlap)
                    })
        
        logic_metrics['overlapping_keywords'] = overlaps
        
        # Calculate mutual exclusivity score
        total_keywords = sum(len(kws) for kws in keyword_sets.values())
        total_overlaps = sum(o['count'] for o in overlaps)
        
        if total_keywords > 0:
            overlap_pct = (total_overlaps / total_keywords * 100)
            logic_metrics['overlap_percentage'] = overlap_pct
            logic_metrics['mutual_exclusivity_score'] = max(0, 100 - overlap_pct)
            
            if overlap_pct > 20:
                logic_metrics['issues'].append(
                    f"High keyword overlap ({overlap_pct:.1f}%) - rules may not be mutually exclusive"
                )
        
        # Calculate logic score
        checks = [
            logic_metrics['mutual_exclusivity_score'] / 100,
            1.0 if logic_metrics['priority_hierarchy_valid'] else 0.0
        ]
        logic_metrics['logic_score'] = (sum(checks) / len(checks)) * 100
        
        return logic_metrics
    
    def _validate_keyword_semantics(self) -> Dict[str, Any]:
        """Step 2.2: Validate semantic correctness of keyword categorization."""
        semantic_metrics = {
            'category_consistency': {},
            'expected_categories': ['Tumor Type', 'Competitors', 'Genotype', 'Research'],
            'category_assignment_score': 0.0,
            'issues': []
        }
        
        # Collect all keywords by category
        category_keywords = {}
        
        if 'relevance_rule' in self.parsed_rules:
            rel_concepts = self.parsed_rules['relevance_rule'].get('key_concepts', {})
            categories = rel_concepts.get('categories', [])
            
            for cat in categories:
                if cat not in category_keywords:
                    category_keywords[cat] = set()
        
        if 'priority_rules' in self.parsed_rules:
            for rule in self.parsed_rules['priority_rules']:
                concepts = rule.get('key_concepts', {})
                categories = concepts.get('categories', [])
                keywords = concepts.get('keywords', [])
                
                for cat in categories:
                    if cat not in category_keywords:
                        category_keywords[cat] = set()
                    category_keywords[cat].update(keywords)
        
        semantic_metrics['category_consistency'] = {
            cat: len(kws) for cat, kws in category_keywords.items()
        }
        
        # Check expected categories
        expected = set(semantic_metrics['expected_categories'])
        present = set(category_keywords.keys())
        
        semantic_metrics['missing_categories'] = list(expected - present)
        semantic_metrics['unexpected_categories'] = list(present - expected)
        
        if semantic_metrics['missing_categories']:
            semantic_metrics['issues'].append(
                f"Missing expected categories: {semantic_metrics['missing_categories']}"
            )
        
        # Calculate category assignment score
        category_score = (len(present & expected) / len(expected)) * 100 if expected else 0
        semantic_metrics['category_assignment_score'] = category_score
        
        return semantic_metrics
    
    def _analyze_exclusions(self) -> Dict[str, Any]:
        """Step 2.3: Analyze exclusion logic."""
        exclusion_metrics = {
            'exclusion_coverage': {},
            'exclusion_effectiveness_score': 0.0,
            'issues': []
        }
        
        if 'priority_rules' not in self.parsed_rules:
            return exclusion_metrics
        
        priority_rules = self.parsed_rules['priority_rules']
        
        # Collect keywords and exclusions by priority
        keyword_sets = {}
        exclusion_sets = {}
        
        for rule in priority_rules:
            priority = rule.get('priority')
            keywords = set(rule.get('key_concepts', {}).get('keywords', []))
            exclusions = set(rule.get('exclusions', []))
            
            keyword_sets[priority] = keywords
            exclusion_sets[priority] = exclusions
        
        # Check if Medium/Low exclusions match High keywords
        if 'High' in keyword_sets:
            high_keywords = keyword_sets['High']
            
            for priority in ['Medium', 'Low']:
                if priority in exclusion_sets:
                    exclusions = exclusion_sets[priority]
                    matched = exclusions & high_keywords
                    
                    exclusion_metrics['exclusion_coverage'][priority] = {
                        'total_exclusions': len(exclusions),
                        'matched_high_keywords': len(matched),
                        'coverage_percentage': (len(matched) / len(exclusions) * 100) if exclusions else 0
                    }
        
        # Calculate effectiveness score
        coverage_scores = [
            info['coverage_percentage'] 
            for info in exclusion_metrics['exclusion_coverage'].values()
        ]
        
        if coverage_scores:
            exclusion_metrics['exclusion_effectiveness_score'] = sum(coverage_scores) / len(coverage_scores)
        
        return exclusion_metrics
    
    def _evaluate_reasoning_quality(self) -> Dict[str, Any]:
        """Step 2.4: Evaluate quality of reasoning provided."""
        reasoning_metrics = {
            'reasoning_completeness': 0.0,
            'reasoning_clarity': 0.0,
            'reasoning_score': 0.0,
            'issues': []
        }
        
        reasoning_texts = []
        
        if 'relevance_rule' in self.parsed_rules:
            reasoning_texts.append(('relevance_rule', self.parsed_rules['relevance_rule'].get('reasoning', '')))
        
        if 'priority_rules' in self.parsed_rules:
            for i, rule in enumerate(self.parsed_rules['priority_rules']):
                priority = rule.get('priority', f'rule_{i}')
                reasoning_texts.append((priority, rule.get('reasoning', '')))
        
        # Completeness check
        completeness_scores = []
        for rule_name, reasoning in reasoning_texts:
            if not reasoning.strip():
                reasoning_metrics['issues'].append(f"{rule_name} has empty reasoning")
                completeness_scores.append(0)
                continue
            
            keywords_mentioned = 'keyword' in reasoning.lower()
            approach_mentioned = 'approach' in reasoning.lower() or 'match' in reasoning.lower()
            logic_mentioned = 'exclusion' in reasoning.lower() or 'priority' in reasoning.lower()
            
            score = sum([keywords_mentioned, approach_mentioned, logic_mentioned]) / 3 * 100
            completeness_scores.append(score)
        
        reasoning_metrics['reasoning_completeness'] = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        # Clarity check
        clarity_scores = []
        for rule_name, reasoning in reasoning_texts:
            length = len(reasoning)
            if 50 <= length <= 500:
                clarity_scores.append(100)
            elif length < 50:
                clarity_scores.append(length / 50 * 100)
            else:
                clarity_scores.append(max(0, 100 - (length - 500) / 10))
        
        reasoning_metrics['reasoning_clarity'] = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0
        
        # Overall reasoning score
        reasoning_metrics['reasoning_score'] = (
            reasoning_metrics['reasoning_completeness'] + 
            reasoning_metrics['reasoning_clarity']
        ) / 2
        
        return reasoning_metrics
    
    def _calculate_semantic_score(self, semantic_metrics: Dict[str, Any]) -> float:
        """Calculate overall semantic score."""
        scores = [
            semantic_metrics['rule_logic']['logic_score'],
            semantic_metrics['keyword_semantics']['category_assignment_score'],
            semantic_metrics['exclusion_analysis'].get('exclusion_effectiveness_score', 50),
            semantic_metrics['reasoning_quality']['reasoning_score']
        ]
        return sum(scores) / len(scores)
    
    # ============================================================================
    # INPUT ALIGNMENT EVALUATION
    # ============================================================================
    
    def evaluate_input_alignment(self) -> Dict[str, Any]:
        """Evaluate alignment between input files and parsed output."""
        logger.info("Running input alignment evaluation")
        
        alignment_metrics = {
            'keyword_coverage': self._check_keyword_coverage(),
            'rule_coverage': self._check_rule_coverage(),
            'alignment_score': 0.0
        }
        
        # Calculate alignment score
        scores = [
            alignment_metrics['keyword_coverage']['coverage_percentage'],
            alignment_metrics['rule_coverage']['coverage_percentage']
        ]
        alignment_metrics['alignment_score'] = sum(scores) / len(scores)
        
        return alignment_metrics
    
    def _check_keyword_coverage(self) -> Dict[str, Any]:
        """Check how many input keywords appear in parsed output."""
        coverage_metrics = {
            'input_keywords_count': len(self.input_keywords),
            'output_keywords_count': 0,
            'matched_keywords_count': 0,
            'coverage_percentage': 0.0,
            'missing_keywords': [],
            'extra_keywords': [],
            'issues': []
        }
        
        # Collect all keywords from parsed output
        output_keywords = set()
        
        if 'relevance_rule' in self.parsed_rules:
            output_keywords.update(
                self.parsed_rules['relevance_rule'].get('key_concepts', {}).get('keywords', [])
            )
        
        if 'priority_rules' in self.parsed_rules:
            for rule in self.parsed_rules['priority_rules']:
                output_keywords.update(
                    rule.get('key_concepts', {}).get('keywords', [])
                )
        
        coverage_metrics['output_keywords_count'] = len(output_keywords)
        
        # Calculate matches
        matched = self.input_keywords & output_keywords
        missing = self.input_keywords - output_keywords
        extra = output_keywords - self.input_keywords
        
        coverage_metrics['matched_keywords_count'] = len(matched)
        coverage_metrics['missing_keywords'] = list(missing)[:20]  # Limit to first 20
        coverage_metrics['extra_keywords'] = list(extra)[:20]
        
        if self.input_keywords:
            coverage_metrics['coverage_percentage'] = (len(matched) / len(self.input_keywords)) * 100
        
        if len(missing) > 0:
            coverage_metrics['issues'].append(
                f"{len(missing)} input keywords not found in parsed output"
            )
        
        return coverage_metrics
    
    def _check_rule_coverage(self) -> Dict[str, Any]:
        """Check if all input rules are represented in parsed output."""
        coverage_metrics = {
            'input_rules_count': len(self.input_rules),
            'output_rules_count': 0,
            'coverage_percentage': 0.0,
            'issues': []
        }
        
        if 'priority_rules' in self.parsed_rules:
            coverage_metrics['output_rules_count'] = len(self.parsed_rules['priority_rules'])
        
        # Simple heuristic: we expect at least 3 priority rules (High, Medium, Low)
        expected_rules = 3
        actual_rules = coverage_metrics['output_rules_count']
        
        if actual_rules >= expected_rules:
            coverage_metrics['coverage_percentage'] = 100.0
        else:
            coverage_metrics['coverage_percentage'] = (actual_rules / expected_rules) * 100
            coverage_metrics['issues'].append(
                f"Expected at least {expected_rules} priority rules, found {actual_rules}"
            )
        
        return coverage_metrics
    
    # ============================================================================
    # OVERALL SCORING & REPORTING
    # ============================================================================
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall evaluation score."""
        scores = []
        
        if 'syntactic' in self.metrics:
            scores.append(self.metrics['syntactic']['syntactic_score'])
        
        if 'semantic' in self.metrics:
            scores.append(self.metrics['semantic']['semantic_score'])
        
        if 'input_alignment' in self.metrics:
            scores.append(self.metrics['input_alignment']['alignment_score'])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _collect_issues(self) -> List[Dict[str, str]]:
        """Collect all issues found during evaluation."""
        all_issues = []
        
        def extract_issues(data, category=''):
            if isinstance(data, dict):
                if 'issues' in data and data['issues']:
                    for issue in data['issues']:
                        all_issues.append({
                            'category': category,
                            'severity': self._determine_severity(issue),
                            'message': issue
                        })
                for key, value in data.items():
                    if key != 'issues':
                        extract_issues(value, f"{category}.{key}" if category else key)
            elif isinstance(data, list):
                for item in data:
                    extract_issues(item, category)
        
        extract_issues(self.metrics)
        return all_issues
    
    def _determine_severity(self, issue: str) -> str:
        """Determine severity of an issue."""
        issue_lower = issue.lower()
        
        if any(word in issue_lower for word in ['missing', 'empty', 'no ']):
            return 'HIGH'
        elif any(word in issue_lower for word in ['incorrect', 'invalid', 'high']):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on evaluation."""
        recommendations = []
        
        if 'syntactic' in self.metrics:
            syn = self.metrics['syntactic']
            
            if syn['schema_validation']['schema_compliance_score'] < 100:
                recommendations.append("Fix schema validation issues - ensure all required fields are present")
            
            if syn['format_consistency']['duplicate_count'] > 0:
                recommendations.append(f"Remove {syn['format_consistency']['duplicate_count']} duplicate keywords")
            
            if syn['format_consistency']['empty_fields_count'] > 0:
                recommendations.append("Fill in empty required fields")
        
        if 'semantic' in self.metrics:
            sem = self.metrics['semantic']
            
            if sem['rule_logic']['overlap_percentage'] > 20:
                recommendations.append("Reduce keyword overlap between priority levels")
            
            if not sem['rule_logic']['priority_hierarchy_valid']:
                recommendations.append("Reorder priority rules to High → Medium → Low")
            
            if sem['keyword_semantics']['missing_categories']:
                recommendations.append(f"Add missing categories: {sem['keyword_semantics']['missing_categories']}")
        
        if 'input_alignment' in self.metrics:
            align = self.metrics['input_alignment']
            
            if align['keyword_coverage']['coverage_percentage'] < 90:
                recommendations.append(
                    f"Low keyword coverage ({align['keyword_coverage']['coverage_percentage']:.1f}%) - "
                    f"{len(align['keyword_coverage']['missing_keywords'])} keywords missing"
                )
        
        if not recommendations:
            recommendations.append("[OK] No major issues found - output looks good!")
        
        return recommendations
    
    def print_summary(self):
        """Print a human-readable summary of evaluation results."""
        if not self.metrics:
            self.evaluate_all()
        
        print("=" * 80)
        print("RULE ANALYSIS EVALUATION REPORT")
        print("=" * 80)
        print(f"\nTimestamp: {self.metrics.get('timestamp', 'N/A')}")
        
        overall = self.metrics.get('overall_score', 0)
        indicator = '[PASS]' if overall >= 80 else '[WARN]' if overall >= 60 else '[FAIL]'
        print(f"\n{indicator} OVERALL SCORE: {overall:.1f}/100")
        
        # Grade
        if overall >= 90:
            grade = "A (Excellent)"
        elif overall >= 80:
            grade = "B (Good)"
        elif overall >= 70:
            grade = "C (Acceptable)"
        elif overall >= 60:
            grade = "D (Needs Improvement)"
        else:
            grade = "F (Poor)"
        
        print(f"   Grade: {grade}")
        print("\n" + "-" * 80)
        
        # Syntactic Summary
        if 'syntactic' in self.metrics:
            print("\n[SYNTACTIC EVALUATION]")
            print("-" * 80)
            syn = self.metrics['syntactic']
            print(f"  Overall: {syn.get('syntactic_score', 0):.1f}/100")
            print(f"  |-- Schema Compliance: {syn['schema_validation']['schema_compliance_score']:.1f}%")
            print(f"  |-- Completeness: {syn['completeness']['completeness_score']:.1f}%")
            print(f"  |-- Format Consistency: {syn['format_consistency']['format_consistency_score']:.1f}%")
            print(f"  +-- Data Quality: {syn['data_quality']['data_quality_score']:.1f}%")
        
        # Semantic Summary
        if 'semantic' in self.metrics:
            print("\n[SEMANTIC EVALUATION]")
            print("-" * 80)
            sem = self.metrics['semantic']
            print(f"  Overall: {sem.get('semantic_score', 0):.1f}/100")
            print(f"  |-- Rule Logic: {sem['rule_logic']['logic_score']:.1f}%")
            print(f"  |-- Mutual Exclusivity: {sem['rule_logic']['mutual_exclusivity_score']:.1f}%")
            print(f"  |-- Category Assignment: {sem['keyword_semantics']['category_assignment_score']:.1f}%")
            print(f"  +-- Reasoning Quality: {sem['reasoning_quality']['reasoning_score']:.1f}%")
        
        # Input Alignment
        if 'input_alignment' in self.metrics:
            print("\n[INPUT ALIGNMENT]")
            print("-" * 80)
            align = self.metrics['input_alignment']
            print(f"  Overall: {align.get('alignment_score', 0):.1f}/100")
            print(f"  |-- Keyword Coverage: {align['keyword_coverage']['coverage_percentage']:.1f}%")
            print(f"  |  ({align['keyword_coverage']['matched_keywords_count']}/{align['keyword_coverage']['input_keywords_count']} keywords)")
            print(f"  +-- Rule Coverage: {align['rule_coverage']['coverage_percentage']:.1f}%")
        
        # Issues
        if 'issues' in self.metrics and self.metrics['issues']:
            print("\n[ISSUES FOUND]")
            print("-" * 80)
            
            high_issues = [i for i in self.metrics['issues'] if i['severity'] == 'HIGH']
            medium_issues = [i for i in self.metrics['issues'] if i['severity'] == 'MEDIUM']
            
            if high_issues:
                print(f"\n  [!] HIGH SEVERITY ({len(high_issues)}):")
                for issue in high_issues[:5]:
                    print(f"     • {issue['message']}")
            
            if medium_issues:
                print(f"\n  [*] MEDIUM SEVERITY ({len(medium_issues)}):")
                for issue in medium_issues[:5]:
                    print(f"     • {issue['message']}")
        
        # Recommendations
        if 'recommendations' in self.metrics and self.metrics['recommendations']:
            print("\n[RECOMMENDATIONS]")
            print("-" * 80)
            for i, rec in enumerate(self.metrics['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 80)
    
    def save_report(self, output_path: str):
        """Save evaluation report to JSON file."""
        if not self.metrics:
            self.evaluate_all()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Evaluation report saved to: {output_path}")


# ============================================================================
# USAGE FUNCTION
# ============================================================================

def evaluate_parsed_rules(
    rules_file: str,
    client_keywords_file: str,
    parsed_rules_file: str,
    custom_synonyms_file: str = None,
    output_report_path: str = None
) -> Dict[str, Any]:
    """
    Main function to evaluate parsed rules.
    
    Args:
        rules_file: Path to rules.csv
        client_keywords_file: Path to client_keywords.csv
        parsed_rules_file: Path to parsed rules JSON file
        custom_synonyms_file: Optional path to custom_synonyms.csv
        output_report_path: Optional path to save evaluation report
    
    Returns:
        Dictionary containing evaluation metrics
    """
    evaluator = RuleAnalysisEvaluator(
        rules_file=rules_file,
        client_keywords_file=client_keywords_file,
        parsed_rules=parsed_rules_file,
        custom_synonyms_file=custom_synonyms_file
    )
    
    metrics = evaluator.evaluate_all()
    evaluator.print_summary()
    
    if output_report_path:
        evaluator.save_report(output_report_path)
    
    return metrics