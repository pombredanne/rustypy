import unittest
import subprocess
import sys
import os
from importlib import import_module

from rustypy.pywrapper import RustFuncGen
from rustypy.rswrapper import load_rust_lib
from rustypy.rswrapper import bind_rs_crate_funcs

def setUpModule():
    global _py_test_dir
    _py_test_dir = os.path.abspath(os.path.dirname(__file__))
    global _rs_lib_dir
    _rs_lib_dir = os.path.join(os.path.dirname(_py_test_dir), 'src', 'rslib')
    # compile rust lib
    load_rust_lib(recmpl=True)

class GenerateRustToPythonBinds(unittest.TestCase):

    def setUp(self):
        if sys.platform.startswith("win"):
            ext = ".dll"
        elif sys.platform == "darwin":
            ext = ".dylib"
        else:
            ext = ".so"
        self.source = os.path.join(_py_test_dir, 'rs_test_lib')
        self.lib_test = os.path.join(
            self.source, 'target', 'debug', 'libtest_lib' + ext)

    #@unittest.skip
    def test_basics_primitives(self):
        bindings = bind_rs_crate_funcs(self.source, self.lib_test)
        # non ref
        return_val, refs = bindings.python_bind_int(1)
        self.assertIsInstance(return_val, int)
        self.assertEqual(return_val, 2)
        # ref
        _, refs = bindings.python_bind_ref_int(1)
        self.assertEqual(refs[0], 2)
        # string
        return_val, _ = bindings.python_bind_str("From Python.")
        self.assertEqual(return_val, "From Python. Added in Rust.")


@unittest.skip
class GeneratePythonToRustBinds(unittest.TestCase):

    def setUp(self):
        self._basics = os.path.join(_rs_lib_dir, 'tests',
            'test_package', 'basics', 'rustypy_pybind.rs')
        self._mod = os.path.join(_rs_lib_dir, 'tests',
            'test_package', 'rustypy_pybind.rs')
        f = open(self._basics, 'w')
        f.close()
        f = open(self._mod, 'w')
        f.close()

    def test_basics_primitives(self):
        self.set_python_path('test_package', 'basics')
        import primitives as test
        self.gen = RustFuncGen(module=test)
        p = subprocess.run(['cargo', 'test', '--test', 'primitives'],
                           cwd=_rs_lib_dir)
        self.assertEqual(p.returncode, 0,
                         'failed Rust integration test `basics_primitives`')

    def test_basics_nested_types(self):
        self.set_python_path('test_package', 'basics')
        import nested_types as test
        self.gen = RustFuncGen(module=test)
        p = subprocess.run(['cargo', 'test', '--test', 'nested_types'],
                           cwd=_rs_lib_dir)
        self.assertEqual(p.returncode, 0,
                         'failed Rust integration test `basics_nested_types`')

    def test_nested_modules(self):
        self.set_python_path()
        init_package = os.path.join(_rs_lib_dir, 'tests',
            'test_package', '__init__.py')
        subprocess.run('python {}'.format(init_package), shell=True)
        p = subprocess.run(['cargo', 'test', '--test', 'submodules'],
                           cwd=_rs_lib_dir)
        self.assertEqual(p.returncode, 0,
                         'failed Rust integration test `nested modules`')

    def set_python_path(self, *path):
        mod_path = os.path.join(_rs_lib_dir, 'tests', *path)
        self._original_path = sys.path.copy()
        sys.path.append(mod_path)

        self._original_env = os.getenv('PYTHONPATH', default="")
        if not self._original_env:
            new_env = mod_path
        else:
            new_env = self._original_env + os.pathsep + mod_path
        os.putenv('PYTHONPATH', new_env)

    def tearDown(self):
        if hasattr(self, '_original_path'):
            sys.path = self._original_path
        if hasattr(self, '_original_env'):
            os.putenv('PYTHONPATH', self._original_env)
        # delete files
        os.remove(self._basics)
        os.remove(self._mod)

if __name__ == "__main__":
    unittest.main()
