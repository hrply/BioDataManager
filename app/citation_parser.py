#!/usr/bin/env python3
"""
BioData Manager - Citation Parser
生物信息学数据管理系统 - 文献引用解析模块

支持解析 BibTeX (.bib)、RIS (.ris)、ENW (.enw) 格式的引文文件
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class CitationParser:
    """文献引用解析器"""
    
    SUPPORTED_FORMATS = ['.bib', '.ris', '.enw']
    
    def __init__(self):
        pass
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """解析引文文件，返回文献信息列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的文献信息列表
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {ext}，仅支持 {', '.join(self.SUPPORTED_FORMATS)}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if ext == '.bib':
            return self._parse_bibtex(content)
        elif ext == '.ris':
            return self._parse_ris(content)
        elif ext == '.enw':
            return self._parse_enw(content)
        
        return []
    
    def parse_content(self, content: str, format_type: str) -> List[Dict[str, Any]]:
        """直接解析内容字符串
        
        Args:
            content: 文件内容
            format_type: 格式类型 (bib, ris, enw)
            
        Returns:
            解析后的文献信息列表
        """
        format_type = format_type.lower()
        
        if format_type == 'bib':
            return self._parse_bibtex(content)
        elif format_type == 'ris':
            return self._parse_ris(content)
        elif format_type == 'enw':
            return self._parse_enw(content)
        else:
            raise ValueError(f"不支持的格式: {format_type}")
    
    def _parse_bibtex(self, content: str) -> List[Dict[str, Any]]:
        """解析 BibTeX 格式"""
        entries = []
        
        # 匹配 @article{...} 或 @book{...} 等条目
        pattern = r'@(\w+)\s*\{\s*([^,]+),([^@]+)\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for entry_type, entry_key, body in matches:
            entry = {
                'type': entry_type.lower(),
                'key': entry_key.strip(),
                'title': self._extract_bibtex_field(body, 'title'),
                'author': self._extract_bibtex_field(body, 'author'),
                'year': self._extract_bibtex_field(body, 'year'),
                'journal': self._extract_bibtex_field(body, 'journal'),
                'volume': self._extract_bibtex_field(body, 'volume'),
                'pages': self._extract_bibtex_field(body, 'pages'),
                'doi': self._extract_bibtex_field(body, 'doi'),
                'abstract': self._extract_bibtex_field(body, 'abstract'),
                'keywords': self._extract_bibtex_field(body, 'keywords'),
            }
            entries.append(entry)
        
        return entries
    
    def _extract_bibtex_field(self, body: str, field_name: str) -> Optional[str]:
        """从 BibTeX 条目中提取字段值"""
        # 匹配 field = {value} 或 field = "value" 或 field = value
        patterns = [
            rf'{field_name}\s*=\s*\{{([^}}]+)\}}',
            rf'{field_name}\s*=\s*"([^"]+)"',
            rf'{field_name}\s*=\s*(\S+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # 清理 LaTeX 特殊字符
                value = re.sub(r'\\[\w]+', '', value)
                return value
        
        return None
    
    def _parse_ris(self, content: str) -> List[Dict[str, Any]]:
        """解析 RIS 格式"""
        entries = []
        current_entry = {}
        
        for line in content.split('\n'):
            if not line.strip():
                continue
            
            # RIS 标签格式: TY  - JOUR
            if line.startswith('TY  -'):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {'type': 'article'}
            elif line.startswith('ER  -'):
                if current_entry:
                    entries.append(current_entry)
                    current_entry = {}
            elif '  - ' in line:
                tag = line[:2].strip()
                value = line[6:].strip() if len(line) > 6 else ''
                
                if tag == 'TI':
                    current_entry['title'] = value
                elif tag == 'AU':
                    if 'author' in current_entry:
                        current_entry['author'] += '; ' + value
                    else:
                        current_entry['author'] = value
                elif tag == 'PY' or tag == 'DA':
                    # 提取年份
                    year_match = re.search(r'(\d{4})', value)
                    current_entry['year'] = year_match.group(1) if year_match else value
                elif tag == 'JO':
                    current_entry['journal'] = value
                elif tag == 'VL':
                    current_entry['volume'] = value
                elif tag == 'SP':
                    current_entry['pages'] = value
                elif tag == 'EP':
                    if 'pages' in current_entry:
                        current_entry['pages'] += '-' + value
                    else:
                        current_entry['pages'] = value
                elif tag == 'DO':
                    current_entry['doi'] = value
                elif tag == 'AB':
                    if 'abstract' in current_entry:
                        current_entry['abstract'] += ' ' + value
                    else:
                        current_entry['abstract'] = value
                elif tag == 'KW':
                    if 'keywords' in current_entry:
                        current_entry['keywords'] += '; ' + value
                    else:
                        current_entry['keywords'] = value
        
        if current_entry:
            entries.append(current_entry)
        
        return entries
    
    def _parse_enw(self, content: str) -> List[Dict[str, Any]]:
        """解析 ENW (EndNote) 格式 - 与 RIS 格式类似"""
        return self._parse_ris(content)
    
    def citation_to_project(self, citation: Dict[str, Any]) -> Dict[str, Any]:
        """将引文信息转换为项目数据
        
        Args:
            citation: 解析后的引文信息
            
        Returns:
            可用于填充项目表单的数据
        """
        # 从作者列表提取第一作者姓氏
        author = citation.get('author', '') or ''
        first_author = author.split(';')[0].strip() if author else ''
        first_author_lastname = first_author.split(',')[0].strip() if first_author else ''
        
        # 清理标题，去除多余空格
        title = citation.get('title', '') or ''
        title = re.sub(r'\s+', ' ', title).strip()
        
        return {
            'raw_title': title,
            'raw_type': 'mRNAseq',  # 默认类型，可由用户修改
            'raw_species': self._detect_species(title + ' ' + (citation.get('abstract', '') or '')),
            'raw_DOI': citation.get('doi', '') or '',
            'raw_article': title,
            'raw_description': citation.get('abstract', '') or '',
            'raw_keywords': citation.get('keywords', '') or '',
        }
    
    def _detect_species(self, text: str) -> str:
        """根据文本内容检测物种"""
        text_lower = text.lower()
        
        if 'human' in text_lower or 'homo sapiens' in text_lower:
            return 'Homo sapiens'
        elif 'mouse' in text_lower or 'mus musculus' in text_lower:
            return 'Mus musculus'
        elif 'rat' in text_lower or 'rattus norvegicus' in text_lower:
            return 'Rattus norvegicus'
        
        return 'Homo sapiens'  # 默认


def parse_citation_file(file_path: str) -> List[Dict[str, Any]]:
    """解析引文文件的便捷函数"""
    parser = CitationParser()
    return parser.parse_file(file_path)


def extract_project_data(citation: Dict[str, Any]) -> Dict[str, Any]:
    """从引文提取项目数据的便捷函数"""
    parser = CitationParser()
    return parser.citation_to_project(citation)


if __name__ == '__main__':
    # 测试解析
    import sys
    
    if len(sys.argv) > 1:
        parser = CitationParser()
        try:
            results = parser.parse_file(sys.argv[1])
            print(f"解析到 {len(results)} 条文献:")
            for i, entry in enumerate(results, 1):
                print(f"\n--- 文献 {i} ---")
                print(f"类型: {entry.get('type', 'N/A')}")
                print(f"标题: {entry.get('title', 'N/A')}")
                print(f"作者: {entry.get('author', 'N/A')}")
                print(f"年份: {entry.get('year', 'N/A')}")
                print(f"期刊: {entry.get('journal', 'N/A')}")
                print(f"DOI: {entry.get('doi', 'N/A')}")
        except Exception as e:
            print(f"解析错误: {e}")
    else:
        print("用法: python citation_parser.py <文件路径>")
        print(f"支持格式: {', '.join(CitationParser.SUPPORTED_FORMATS)}")
