# usage: python3 wrap.py <dir> <title>  -- wraps <dir>/scene.js into <dir>/motion.html
import sys
d, title = sys.argv[1], sys.argv[2]
head = open('../second-brain/a/motion.html').read()
head = head[:head.index('<script src="../common/lib.js"></script>') + len('<script src="../common/lib.js"></script>')]
head = head.replace('<title>Second Brain A</title>', f'<title>{title}</title>')
open(f'{d}/motion.html', 'w').write(head + '\n<script>\n' + open(f'{d}/scene.js').read() + '\n</script>\n</body>\n</html>\n')
