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
        (pkgs.python3.withPackages (py-pkgs:
          with py-pkgs; [
            pyopengl
            pygame
          ]))
      ];
    };
    packages.${system}.default = with pkgs.python3Packages;
      buildPythonPackage {
        pname = "pyopenglWrapper";
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
