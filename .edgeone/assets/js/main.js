/**
 * 英语学习新闻博客 - 主脚本
 * Gitee Pages - News Blog
 */

(function() {
    'use strict';

    // 添加单词点击交互
    function initWordInteraction() {
        const words = document.querySelectorAll('.english-word');

        words.forEach(function(word) {
            word.addEventListener('click', function() {
                const wordText = this.textContent.trim();
                // 可以在这里添加更多交互，比如播放发音、显示详细释义等
                console.log('点击单词:', wordText);
            });
        });
    }

    // 平滑滚动
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // 词汇表搜索功能
    function initVocabSearch() {
        const vocabTable = document.querySelector('.vocab-table');
        if (!vocabTable) return;

        // 创建搜索框
        const searchContainer = document.createElement('div');
        searchContainer.style.cssText = 'margin: 15px 0;';
        searchContainer.innerHTML = '<input type="text" id="vocab-search" placeholder="🔍 搜索单词..." style="padding: 10px 15px; border: 2px solid #667eea; border-radius: 25px; width: 100%; max-width: 300px; font-size: 14px; outline: none;">';

        const subtitle = document.querySelector('.subtitle');
        if (subtitle) {
            subtitle.insertAdjacentElement('afterend', searchContainer);
        }

        const searchInput = document.getElementById('vocab-search');
        const tableRows = vocabTable.querySelectorAll('tbody tr');

        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();

            tableRows.forEach(function(row) {
                const word = row.cells[0].textContent.toLowerCase();
                const meaning = row.cells[2].textContent.toLowerCase();

                if (word.includes(query) || meaning.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 初始化
    function init() {
        initWordInteraction();
        initSmoothScroll();
        initVocabSearch();

        console.log('📚 英语学习博客已加载');
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
