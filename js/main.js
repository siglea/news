/**
 * 英语学习新闻博客 - 主脚本
 * Gitee Pages - News Blog
 */

(function() {
    'use strict';

    /**
     * 正文内词汇释义：默认隐藏，鼠标悬停 / 键盘聚焦 / 点击英文词展开浮层；点击空白或 Esc 关闭。
     */
    function initWordGlossPopovers() {
        var root = document.querySelector('.post-content');
        if (!root) return;

        var blocks = root.querySelectorAll('.word-block');
        if (!blocks.length) return;

        function closeAll() {
            blocks.forEach(function(b) {
                b.classList.remove('word-block--open');
            });
        }

        blocks.forEach(function(block) {
            var trigger = block.querySelector('.english-word');
            if (!trigger) return;

            trigger.setAttribute('tabindex', '0');
            trigger.setAttribute('role', 'button');

            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var wasOpen = block.classList.contains('word-block--open');
                closeAll();
                if (!wasOpen) {
                    block.classList.add('word-block--open');
                }
            });

            trigger.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    trigger.click();
                }
            });
        });

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.post-content .word-block')) {
                closeAll();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeAll();
            }
        });
    }

    // 平滑滚动
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                var target = document.querySelector(this.getAttribute('href'));
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
        var vocabTable = document.querySelector('.vocab-table');
        if (!vocabTable) return;

        var searchContainer = document.createElement('div');
        searchContainer.style.cssText = 'margin: 15px 0;';
        searchContainer.innerHTML = '<input type="text" id="vocab-search" placeholder="🔍 搜索单词..." style="padding: 10px 15px; border: 2px solid #667eea; border-radius: 25px; width: 100%; max-width: 300px; font-size: 14px; outline: none;">';

        var subtitle = document.querySelector('.subtitle');
        if (subtitle) {
            subtitle.insertAdjacentElement('afterend', searchContainer);
        }

        var searchInput = document.getElementById('vocab-search');
        var tableRows = vocabTable.querySelectorAll('tbody tr');

        searchInput.addEventListener('input', function() {
            var query = this.value.toLowerCase();

            tableRows.forEach(function(row) {
                var word = row.cells[0].textContent.toLowerCase();
                var meaning = row.cells[2].textContent.toLowerCase();

                if (word.includes(query) || meaning.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    function init() {
        initWordGlossPopovers();
        initSmoothScroll();
        initVocabSearch();

        console.log('📚 英语学习博客已加载');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
