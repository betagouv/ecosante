from webassets.filter import FilterError
from webassets.filter.sass import Sass
from webassets.filter.node_sass import NodeSCSS
from webassets.ext.jinja2 import AssetsExtension
import os
import subprocess
from webassets.filter import (
    get_filter,
    register_filter
)

class YarnSCSS(NodeSCSS):
    name = 'yarn-scss'
    def __init__(self, *a, **kw):
        super(YarnSCSS, self).__init__(*a, **kw)

    def _apply_sass(self, _in, out, cd=None):
        args = ['yarn', 'run', 'node-scss', 
        '--output-style', 'expanded']

        if (self.ctx.environment.debug if self.debug_info is None else self.debug_info):
            args.append('--debug-info')

        proc = subprocess.Popen(args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=(os.name == 'nt'))
        stdout, stderr = proc.communicate(_in.read().encode('utf-8'))

        if proc.returncode != 0:
            raise FilterError(('sass: subprocess had error: stderr=%s, '+
                                'stdout=%s, returncode=%s') % (
                                            stderr, stdout, proc.returncode))
        elif stderr:
            print("node-sass filter has warnings:", stderr)

        out.write(stdout.decode('utf-8'))


class Rollup(Sass):
    options = {
        'binary': 'ROLLUP_BIN',
        'as_output': 'ROLLUP_OUTPUT',
        'load_paths': 'ROLLUP_LOAD_PATHS',
    }
    args = []
    binary = "yarn"

    def _apply_sass(self, _in, out, cd=None):
        orig_cwd = os.getcwd()
        child_cwd = orig_cwd
        if cd:
            child_cwd = cd

        for path in self.load_paths or []:
            if os.path.isabs(path):
                abs_path = path
            else:
                abs_path = self.resolve_path(path)
            self.args.extend(['-f', abs_path])
        return self.subprocess(self.args, out, _in, cwd=child_cwd)


class RollupJS(Rollup):
    name='rollupjs'
    def __init__(self, *args, **kwargs):
        super(RollupJS, self).__init__(*args, **kwargs)
        self.binary = RollupJS.binary
        self.args = [
            self.binary or 'rollup',
            'run',
            'rollup',
            '-f', 'iife',
            "-p", "'commonjs,postcss'",
            "-p", '"{{babel:{{babelHelpers:\'bundled\', exclude: \'node_modules/**\'}}}}"',
            "-p", "'node-resolve'",
        ]


class RollupJSExtension(AssetsExtension):
    tags=set(['rollupjs'])

    def __init__(self, environment):
        super(RollupJSExtension, self).__init__(environment)

    def _render_assets(self, filter, output, dbg, depends, files, caller=None):
        return super(RollupJSExtension, self)._render_assets(
            "rollupjs",
            os.path.join("public", files[0]),
            dbg,
            depends,
            files,
            caller
        )

class SCSSExtension(AssetsExtension):
    tags=set(['scss'])

    def __init__(self, environment):
        super(SCSSExtension, self).__init__(environment)

    def _render_assets(self, filter, output, dbg, depends, files, caller=None):
        return super(SCSSExtension, self)._render_assets(
            "yarn-scss",
            os.path.join("public", files[0]).replace(".scss", ".css"),
            dbg,
            depends,
            files,
            caller
        )


try:
    get_filter(RollupJS.name)
    get_filter(YarnSCSS.name)
except ValueError:
    register_filter(RollupJS)
    register_filter(YarnSCSS)