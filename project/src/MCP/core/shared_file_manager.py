import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
import hashlib
from datetime import datetime, timedelta

@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: str
    original_path: str
    cached_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    accessed_at: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

class SharedFileManager:
    """共享文件管理器"""
    
    def __init__(self, base_dir: str = "/data/Tiaozhanbei/shared"):
        self.base_dir = Path(base_dir)
        self.logger = logging.getLogger(__name__)
        
        # 创建必要的目录结构
        self._create_directory_structure()
        
        # 文件缓存
        self.file_cache: Dict[str, FileMetadata] = {}
        self.file_index_path = self.base_dir / "file_index.json"
        
        # 加载现有文件索引
        self._load_file_index()
        
        # 启动清理任务
        self._start_cleanup_task()
    
    def _create_directory_structure(self):
        """创建目录结构"""
        directories = [
            "input",
            "output", 
            "temp",
            "cache",
            "climada",
            "lisflood",
            "pangu_weather",
            "nfdrs4",
            "cell2fire",
            "aurora"
        ]
        
        for dir_name in directories:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_file_index(self):
        """加载文件索引"""
        if self.file_index_path.exists():
            try:
                with open(self.file_index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    
                    for file_id, file_data in index_data.items():
                        # 转换日期字符串为datetime对象
                        file_data['created_at'] = datetime.fromisoformat(file_data['created_at'])
                        file_data['accessed_at'] = datetime.fromisoformat(file_data['accessed_at'])
                        if file_data.get('expires_at'):
                            file_data['expires_at'] = datetime.fromisoformat(file_data['expires_at'])
                        
                        self.file_cache[file_id] = FileMetadata(**file_data)
                        
            except Exception as e:
                self.logger.error(f"Failed to load file index: {e}")
    
    def _save_file_index(self):
        """保存文件索引"""
        try:
            index_data = {}
            for file_id, metadata in self.file_cache.items():
                index_data[file_id] = {
                    'file_id': metadata.file_id,
                    'original_path': metadata.original_path,
                    'cached_path': metadata.cached_path,
                    'file_size': metadata.file_size,
                    'mime_type': metadata.mime_type,
                    'created_at': metadata.created_at.isoformat(),
                    'accessed_at': metadata.accessed_at.isoformat(),
                    'expires_at': metadata.expires_at.isoformat() if metadata.expires_at else None,
                    'tags': metadata.tags or [],
                    'metadata': metadata.metadata or {}
                }
            
            with open(self.file_index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save file index: {e}")
    
    def _generate_file_id(self, file_path: str, content_hash: Optional[str] = None) -> str:
        """生成文件ID"""
        if content_hash:
            return f"{content_hash}_{int(datetime.now().timestamp())}"
        else:
            # 使用文件路径和修改时间生成ID
            path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
            return f"{path_hash}_{int(datetime.now().timestamp())}"
    
    def _get_mime_type(self, file_path: str) -> str:
        """获取MIME类型"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    async def cache_file(
        self,
        file_path: str,
        target_dir: str = "temp",
        tags: Optional[List[str]] = None,
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """缓存文件到共享目录"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            # 计算文件哈希
            content_hash = await self._calculate_file_hash(source_path)
            
            # 生成文件ID
            file_id = self._generate_file_id(file_path, content_hash)
            
            # 检查是否已经缓存
            if content_hash in [meta.metadata.get('content_hash') for meta in self.file_cache.values()]:
                # 文件已缓存，返回现有ID
                for fid, meta in self.file_cache.items():
                    if meta.metadata.get('content_hash') == content_hash:
                        # 更新访问时间
                        meta.accessed_at = datetime.now()
                        self._save_file_index()
                        return fid
            
            # 确定目标目录
            target_path = self.base_dir / target_dir
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            cached_path = target_path / f"{file_id}_{source_path.name}"
            shutil.copy2(source_path, cached_path)
            
            # 创建文件元数据
            file_metadata = FileMetadata(
                file_id=file_id,
                original_path=str(source_path),
                cached_path=str(cached_path),
                file_size=cached_path.stat().st_size,
                mime_type=self._get_mime_type(str(source_path)),
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=expires_in_hours) if expires_in_hours else None,
                tags=tags or [],
                metadata={
                    'content_hash': content_hash,
                    'original_name': source_path.name,
                    **(metadata or {})
                }
            )
            
            # 添加到缓存
            self.file_cache[file_id] = file_metadata
            self._save_file_index()
            
            self.logger.info(f"File cached: {file_id} -> {cached_path}")
            return file_id
            
        except Exception as e:
            self.logger.error(f"Failed to cache file {file_path}: {e}")
            raise
    
    async def get_cached_file(self, file_id: str) -> Optional[FileMetadata]:
        """获取缓存的文件信息"""
        if file_id not in self.file_cache:
            return None
        
        metadata = self.file_cache[file_id]
        
        # 检查文件是否过期
        if metadata.expires_at and datetime.now() > metadata.expires_at:
            await self.remove_cached_file(file_id)
            return None
        
        # 检查文件是否仍然存在
        if not Path(metadata.cached_path).exists():
            await self.remove_cached_file(file_id)
            return None
        
        # 更新访问时间
        metadata.accessed_at = datetime.now()
        self._save_file_index()
        
        return metadata
    
    async def remove_cached_file(self, file_id: str) -> bool:
        """移除缓存的文件"""
        if file_id not in self.file_cache:
            return False
        
        try:
            metadata = self.file_cache[file_id]
            
            # 删除文件
            cached_path = Path(metadata.cached_path)
            if cached_path.exists():
                cached_path.unlink()
            
            # 从缓存中移除
            del self.file_cache[file_id]
            self._save_file_index()
            
            self.logger.info(f"Removed cached file: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove cached file {file_id}: {e}")
            return False
    
    async def list_cached_files(
        self,
        tags: Optional[List[str]] = None,
        mime_type: Optional[str] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None
    ) -> List[FileMetadata]:
        """列出缓存的文件"""
        files = []
        
        for metadata in self.file_cache.values():
            # 检查标签
            if tags and not all(tag in (metadata.tags or []) for tag in tags):
                continue
            
            # 检查MIME类型
            if mime_type and metadata.mime_type != mime_type:
                continue
            
            # 检查文件大小
            if size_min and metadata.file_size < size_min:
                continue
            if size_max and metadata.file_size > size_max:
                continue
            
            files.append(metadata)
        
        # 按访问时间排序
        files.sort(key=lambda x: x.accessed_at, reverse=True)
        return files
    
    async def cleanup_expired_files(self) -> int:
        """清理过期的文件"""
        expired_files = []
        now = datetime.now()
        
        for file_id, metadata in self.file_cache.items():
            if metadata.expires_at and now > metadata.expires_at:
                expired_files.append(file_id)
        
        removed_count = 0
        for file_id in expired_files:
            if await self.remove_cached_file(file_id):
                removed_count += 1
        
        self.logger.info(f"Cleaned up {removed_count} expired files")
        return removed_count
    
    async def cleanup_old_files(self, days: int = 7) -> int:
        """清理旧文件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_files = []
        
        for file_id, metadata in self.file_cache.items():
            if metadata.accessed_at < cutoff_date:
                old_files.append(file_id)
        
        removed_count = 0
        for file_id in old_files:
            if await self.remove_cached_file(file_id):
                removed_count += 1
        
        self.logger.info(f"Cleaned up {removed_count} old files")
        return removed_count
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        async def cleanup_loop():
            while True:
                try:
                    # 每小时清理一次过期文件
                    await self.cleanup_expired_files()
                    
                    # 每天清理一次旧文件
                    if datetime.now().hour == 2:  # 凌晨2点
                        await self.cleanup_old_files()
                    
                    await asyncio.sleep(3600)  # 等待1小时
                    
                except Exception as e:
                    self.logger.error(f"Cleanup task error: {e}")
                    await asyncio.sleep(3600)
        
        # 启动后台任务
        asyncio.create_task(cleanup_loop())
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        total_size = sum(meta.file_size for meta in self.file_cache.values())
        file_count = len(self.file_cache)
        
        # 按类型统计
        type_stats = {}
        for metadata in self.file_cache.values():
            mime_type = metadata.mime_type
            if mime_type not in type_stats:
                type_stats[mime_type] = {'count': 0, 'size': 0}
            type_stats[mime_type]['count'] += 1
            type_stats[mime_type]['size'] += metadata.file_size
        
        # 按标签统计
        tag_stats = {}
        for metadata in self.file_cache.values():
            for tag in (metadata.tags or []):
                if tag not in tag_stats:
                    tag_stats[tag] = {'count': 0, 'size': 0}
                tag_stats[tag]['count'] += 1
                tag_stats[tag]['size'] += metadata.file_size
        
        return {
            'total_files': file_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'type_statistics': type_stats,
            'tag_statistics': tag_stats,
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率（简化实现）"""
        # 这里可以实现更复杂的缓存命中率计算
        return 0.85  # 示例值
    
    async def close(self):
        """关闭文件管理器"""
        self._save_file_index()
        self.logger.info("Shared file manager closed")
