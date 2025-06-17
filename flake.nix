{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixpkgs-unstable";
  };

  outputs = {nixpkgs, ...}: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {inherit system;};
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [
        (python3WithPackages (py-pkgs:
          with py-pkgs; [
            pyopengl
            pygame
          ]))
      ];
    };
    packages.${system}.default = with pkgs.python3Packages;
      buildPythonPackage {
        pname = "pyopengl-wrapper";
        version = "0.1";
        src = ./.;
        propagatedBuildInputs = [
          setuptools
          pyopengl
          pygame
        ];
        pyproject = true;
      };
  };
}
