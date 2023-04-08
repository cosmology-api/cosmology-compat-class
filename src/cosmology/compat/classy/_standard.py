"""The Cosmology API compatability wrapper for CAMB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy import vectorize

from cosmology.compat.classy import constants
from cosmology.compat.classy._core import CosmologyWrapper, InputT, NDFloating

__all__: list[str] = []


_MPCS_KM_TO_GYR = np.array("978.5", dtype=np.float64)  # [Mpc s / km -> Gyr]


@dataclass(frozen=True)
class StandardCosmologyWrapper(CosmologyWrapper):
    """FLRW Cosmology API wrapper for CAMB cosmologies."""

    def __post_init__(self) -> None:
        """Run-time post-processing.

        Note that if this module is c-compiled (e.g. with :mod:`mypyc`) that
        the type of ``self.cosmo`` must be ``CAMBdata`` at object creation
        and cannot be later processed here.
        """
        super().__post_init__()

        self._cosmo_fn: dict[str, Any]
        object.__setattr__(
            self,
            "_cosmo_fn",
            {
                "Om_m": vectorize(self.cosmo.Om_m),
                "Hubble": vectorize(self.cosmo.Hubble),
                "angular_distance": vectorize(self.cosmo.angular_distance),
                "luminosity_distance": vectorize(self.cosmo.luminosity_distance),
            },
        )

    # ----------------------------------------------
    # HasTotalComponent

    @property
    def Omega_tot0(self) -> NDFloating:
        r"""Omega total; the total density/critical density at z=0.

        Note this should alway be 1.

        .. math::

            \Omega_{\rm tot} = \Omega_{\rm m} + \Omega_{\rm r} + \Omega_{\rm de}
            + \Omega_{\rm k}
        """
        return np.array(
            self.cosmo.Omega_Lambda()
            + self.cosmo.Omega_m()
            + self.cosmo.Omega0_k()
            + self.cosmo.Omega_r()
        )

    def Omega_tot(self, z: InputT, /) -> NDFloating:
        r"""Redshift-dependent total density parameter.

        This is the sum of the matter, radiation, neutrino, dark energy, and
        curvature density parameters.

        .. math::

            \Omega_{\rm tot} = \Omega_{\rm m} + \Omega_{\rm \gamma} +
            \Omega_{\rm \nu} + \Omega_{\rm de} + \Omega_{\rm k}
        """
        raise NotImplementedError
        #  Basically just return np.ones_like(z)

    # ----------------------------------------------
    # HasGlobalCurvatureComponent

    @property
    def Omega_k0(self) -> NDFloating:
        """Omega curvature; the effective curvature density/critical density at z=0."""
        return np.asarray(self.cosmo.Omega0_k())

    def Omega_k(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent curvature density parameter."""
        raise NotImplementedError

    # ----------------------------------------------
    # HasMatterComponent

    @property
    def Omega_m0(self) -> NDFloating:
        """Matter density at z=0."""
        return np.asarray(self.cosmo.Omega_m())

    def Omega_m(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent non-relativistic matter density parameter.

        Notes
        -----
        This does not include neutrinos, even if non-relativistic at the
        redshift of interest; see `Onu`.
        """
        return np.asarray(self._cosmo_fn["Om_m"](z))

    # ----------------------------------------------
    # HasBaryonComponent

    @property
    def Omega_b0(self) -> NDFloating:
        """Baryon density at z=0."""
        return np.asarray(self.cosmo.Omega_b())

    def Omega_b(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent baryon density parameter.

        Raises
        ------
        ValueError
            If ``Ob0`` is `None`.
        """
        raise NotImplementedError

    # ----------------------------------------------
    # HasNeutrinoComponent

    @property
    def Omega_nu0(self) -> NDFloating:
        """Omega nu; the density/critical density of neutrinos at z=0."""
        raise NotImplementedError

    @property
    def Neff(self) -> NDFloating:
        """Effective number of neutrino species."""
        return np.asarray(self.cosmo.Neff())

    @property
    def m_nu(self) -> tuple[NDFloating, ...]:
        """Neutrino mass in eV."""
        raise NotImplementedError

    def Omega_nu(self, z: InputT, /) -> NDFloating:
        r"""Redshift-dependent neutrino density parameter."""
        raise NotImplementedError

    # ----------------------------------------------
    # HasDarkEnergyComponent

    @property
    def Omega_de0(self) -> NDFloating:
        """Dark energy density at z=0."""
        return np.asarray(self.cosmo.Omega_Lambda())

    def Omega_de(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent dark energy density parameter."""
        raise NotImplementedError

    # ----------------------------------------------
    # HasDarkMatterComponent

    @property
    def Omega_dm0(self) -> NDFloating:
        """Omega dark matter; dark matter density/critical density at z=0."""
        return np.asarray(self.cosmo.Omega0_cdm())

    def Omega_dm(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent dark matter density parameter.

        Notes
        -----
        This does not include neutrinos, even if non-relativistic at the
        redshift of interest.
        """
        raise NotImplementedError

    # ----------------------------------------------
    # HasPhotonComponent

    @property
    def Omega_gamma0(self) -> NDFloating:
        """Omega gamma; the density/critical density of photons at z=0."""
        return np.asarray(self.cosmo.Omega_g())

    def Omega_gamma(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent photon density parameter."""
        raise NotImplementedError

    # ----------------------------------------------
    # HasCriticalDensity

    @property
    def critical_density0(self) -> NDFloating:
        """Critical density at z = 0 in Msol Mpc-3."""
        return np.array(3e6 * self.H0**2 / (8 * np.pi * constants.G))

    def critical_density(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent critical density in Msol Mpc-3."""
        return np.array(3e6 * self.H(z) ** 2 / (8 * np.pi * constants.G))

    # ----------------------------------------------
    # HasHubbleParameter

    @property
    def H0(self) -> NDFloating:
        """Hubble constant at z=0 in km s-1 Mpc-1."""
        return np.array(constants.c * self.cosmo.Hubble(0))

    @property
    def hubble_distance(self) -> NDFloating:
        """Hubble distance in Mpc."""
        return np.array(1 / self.cosmo.Hubble(0))

    @property
    def hubble_time(self) -> NDFloating:
        """Hubble time in Gyr."""
        return np.array(_MPCS_KM_TO_GYR / self.H0)

    def H(self, z: InputT, /) -> NDFloating:
        """Hubble function :math:`H(z)` in km s-1 Mpc-1."""  # noqa: D402
        return np.array(constants.c * self._cosmo_fn["Hubble"](z))

    def h_over_h0(self, z: InputT, /) -> NDFloating:
        """Standardised Hubble function :math:`E(z) = H(z)/H_0`."""
        return self._cosmo_fn["Hubble"](z) / self.cosmo.Hubble(0)

    # ----------------------------------------------
    # Scale factor

    @property
    def scale_factor0(self) -> NDFloating:
        """Scale factor at z=0."""
        return np.asarray(1.0)

    def scale_factor(self, z: InputT, /) -> NDFloating:
        """Redshift-dependenct scale factor :math:`a = a_0 / (1 + z)`."""
        return np.asarray(self.scale_factor0 / (z + 1))

    # ----------------------------------------------
    # Temperature

    @property
    def Tcmb0(self) -> NDFloating:
        """Temperature of the CMB at z=0."""
        return np.asarray(self.cosmo.T_cmb())

    def Tcmb(self, z: InputT, /) -> NDFloating:
        """Temperature of the CMB at redshift ``z``."""
        return self.Tcmb0 * (z + 1)

    # ----------------------------------------------
    # Time

    def age(self, z: InputT, /) -> NDFloating:
        """Age of the universe in Gyr at redshift ``z``."""
        raise NotImplementedError

    def lookback_time(self, z: InputT, /) -> NDFloating:
        """Lookback time to redshift ``z`` in Gyr.

        The lookback time is the difference between the age of the Universe now
        and the age at redshift ``z``.
        """
        raise NotImplementedError

    # ----------------------------------------------
    # Comoving distance

    def comoving_distance(self, z: InputT, /) -> NDFloating:
        r"""Comoving line-of-sight distance :math:`d_c(z)` in Mpc.

        The comoving distance along the line-of-sight between two objects
        remains constant with time for objects in the Hubble flow.
        """
        raise NotImplementedError

    def comoving_transverse_distance(self, z: InputT, /) -> NDFloating:
        r"""Transverse comoving distance :math:`d_M(z)` in Mpc.

        This value is the transverse comoving distance at redshift ``z``
        corresponding to an angular separation of 1 radian. This is the same as
        the comoving distance if :math:`\Omega_k` is zero (as in the current
        concordance Lambda-CDM model).
        """
        raise NotImplementedError

    def _comoving_volume_flat(self, z: InputT, /) -> NDFloating:
        return 4.0 / 3.0 * np.pi * self.comoving_distance(z) ** 3

    def _comoving_volume_positive(self, z: InputT, /) -> NDFloating:
        dh = self.hubble_distance
        x = self.comoving_transverse_distance(z) / dh
        term1 = 4.0 * np.pi * dh**3 / (2.0 * self.Omega_k0)
        term2 = x * np.sqrt(1 + self.Omega_k0 * (x) ** 2)
        term3 = np.sqrt(np.abs(self.Omega_k0)) * x

        return term1 * (
            term2 - 1.0 / np.sqrt(np.abs(self.Omega_k0)) * np.arcsinh(term3)
        )

    def _comoving_volume_negative(self, z: InputT, /) -> NDFloating:
        dh = self.hubble_distance
        x = self.comoving_transverse_distance(z) / dh
        term1 = 4.0 * np.pi * dh**3 / (2.0 * self.Omega_k0)
        term2 = x * np.sqrt(1 + self.Omega_k0 * (x) ** 2)
        term3 = np.sqrt(np.abs(self.Omega_k0)) * x
        return term1 * (term2 - 1.0 / np.sqrt(np.abs(self.Omega_k0)) * np.arcsin(term3))

    def comoving_volume(self, z: InputT, /) -> NDFloating:
        r"""Comoving volume in cubic Mpc.

        This is the volume of the universe encompassed by redshifts less than
        ``z``. For the case of :math:`\Omega_k = 0` it is a sphere of radius
        `comoving_distance` but it is less intuitive if :math:`\Omega_k` is not.
        """
        if self.Omega_k0 == 0:
            cv = self._comoving_volume_flat(z)
        elif self.Omega_k0 > 0:
            cv = self._comoving_volume_positive(z)
        else:
            cv = self._comoving_volume_negative(z)
        return cv

    def differential_comoving_volume(self, z: InputT, /) -> NDFloating:
        r"""Differential comoving volume in cubic Mpc per steradian.

        If :math:`V_c` is the comoving volume of a redshift slice with solid
        angle :math:`\Omega`, this function ...

        .. math::

            \mathtt{dvc(z)}
            = \frac{1}{d_H^3} \, \frac{dV_c}{d\Omega \, dz}
            = \frac{x_M^2(z)}{E(z)}
            = \frac{\mathtt{xm(z)^2}}{\mathtt{ef(z)}} \;.

        """
        return (
            self.comoving_transverse_distance(z) / self.hubble_distance
        ) ** 2 / self.h_over_h0(z)

    # ----------------------------------------------
    # Angular diameter distance

    def angular_diameter_distance(self, z: InputT, /) -> NDFloating:
        """Angular diameter distance :math:`d_A(z)` in Mpc.

        This gives the proper (sometimes called 'physical') transverse
        distance corresponding to an angle of 1 radian for an object
        at redshift ``z`` ([1]_, [2]_, [3]_).

        References
        ----------
        .. [1] Weinberg, 1972, pp 420-424; Weedman, 1986, pp 421-424.
        .. [2] Weedman, D. (1986). Quasar astronomy, pp 65-67.
        .. [3] Peebles, P. (1993). Principles of Physical Cosmology, pp 325-327.
        """
        return np.asarray(self._cosmo_fn["angular_distance"](z))

    # ----------------------------------------------
    # Luminosity distance

    def luminosity_distance(self, z: InputT, /) -> NDFloating:
        """Redshift-dependent luminosity distance in Mpc.

        This is the distance to use when converting between the bolometric flux
        from an object at redshift ``z`` and its bolometric luminosity [1]_.

        References
        ----------
        .. [1] Weinberg, 1972, pp 420-424; Weedman, 1986, pp 60-62.
        """
        return np.asarray(self._cosmo_fn["luminosity_distance"](z))