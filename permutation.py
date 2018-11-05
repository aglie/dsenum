import numpy as np

from smith_normal_form import smith_normal_form


class Permutation(object):
    """
    Parameters
    ----------
    hnf: array, (dim, dim)
        Hermite normal form
    num_site_parent: int
        # of atoms in parent multilattice
    displacement_set: array, (num_site_parent, dim)
        fractinal coordinates of A in multilattice site
    rotations: array, (# of symmetry operations, dim, dim)
        rotations in fractinal coordinations of A
    translations: array, (# of symmetry operations, dim)
        translations in fractinal coordinations of A

    Attributes
    ----------
    dim : int
        dimention of lattice
    index: int
        # of parent multilattice in super lattice
    num_site: int
        # of sites in unit cell of superlattice
    shape: tuple of int
        (1 + dim, num_site)
    snf: array, (dim, dim)
        Smith normal form
    left: array, (dim, dim)
        left unimodular matrix
    left_inv: array, (dim, dim)
        inverse of left matrix
    right: array, (dim, dim)
        right unimodular matrix
    factors_e: array, (1 + dim, num_site)
    parent_frac_coords_e: array (dim, num_site)
    """
    def __init__(self, hnf, num_site_parent=1, displacement_set=None,
                 rotations=None, translations=None):
        self.hnf = hnf
        self.hnf_inv = np.linalg.inv(self.hnf)
        self.dim = self.hnf.shape[0]
        self.index = np.prod(self.hnf.diagonal())

        self.num_site_parent = num_site_parent
        self.num_site = self.index * self.num_site_parent

        if self.num_site_parent == 1:
            self.displacement_set = np.array([[0, 0, 0]])
        else:
            self.displacement_set = displacement_set
            assert self.displacement_set.shape[0] == self.num_site_parent

        D, L, R = smith_normal_form(self.hnf)
        self.snf = D
        self.left = L
        self.left_inv = np.around(np.linalg.inv(self.left)).astype(np.int)
        self.right = R

        self.shape = tuple([self.num_site_parent]
                           + self.snf.diagonal().tolist())

        # (1 + dim, num_site)
        self.factors_e = np.array([np.unravel_index(indices, self.shape)
                                   for indices in range(self.num_site)]).T
        # (dim, num_site)
        self.parent_frac_coords_e = self.displacement_set[self.factors_e[0, :]].T \
            + np.dot(self.left_inv, self.factors_e[1:, :])

        self.rotations, self.translations = \
            self._get_superlattice_symmetry_operations(rotations, translations)

    def _get_superlattice_symmetry_operations(self,
                                              rotations, translations):
        """
        return symmetry operations of superlattice
        """
        valid_rotations = []
        valid_translations = []
        self.prm_rigid = []

        for R, tau in zip(rotations, translations):
            if not is_same_lattice(np.dot(R, self.hnf), self.hnf):
                continue

            # (dim, num_site)
            parent_frac_coords = np.dot(R, self.parent_frac_coords_e) \
                + tau[:, np.newaxis]
            dset = np.fmod(parent_frac_coords,
                           np.ones(self.dim)[:, np.newaxis])
            lattice_factors = np.dot(self.left,
                                     np.around(parent_frac_coords - dset).astype(np.int))
            lattice_factors = np.mod(lattice_factors,
                                     np.array(self.shape[1:])[:, np.newaxis])

            factors = -np.ones_like(self.factors_e)
            factors[1:, :] = lattice_factors
            # TODO: awkward
            for i in range(self.num_site):
                for j, ds in enumerate(self.displacement_set):
                    if np.array_equal(dset[:, i], ds):
                        factors[0, i] = j
                        break

            # if lattice_factors.shape[1] != np.unique(lattice_factors, axis=1).shape[1]:
            #     continue
            # if np.any(factors[0, :] == -1):
            #     continue

            raveled_factors = np.ravel_multi_index(factors, self.shape)
            self.prm_rigid.append(raveled_factors)
            print(raveled_factors)

            valid_rotations.append(R)
            valid_translations.append(tau)

        return np.array(valid_rotations), np.array(valid_translations)

    def get_translation_permutations(self):
        list_permutations = []
        for i in range(self.num_site):
            di = np.dot(self.left, self.factors_e[:, i])
            factors = np.mod(self.factors_e + di[:, np.newaxis],
                             np.array(self.shape)[:, np.newaxis])
            raveled_factors = np.ravel_multi_index(factors, self.shape)
            list_permutations.append(tuple(raveled_factors.tolist()))
        assert self.validate_permutations(list_permutations)
        return list_permutations

    def get_symmetry_operation_permutaions(self):
        if self.rotations is None:
            return self.prm_t

        list_permutations = []

        for i in range(self.num):
            for factors_r in self.rotation_factors:
                di = self.factors_e[:, i]
                factors = np.mod(factors_r + di[:, np.newaxis],
                                 np.array(self.shape)[:, np.newaxis])
                raveled_factors = tuple(np.ravel_multi_index(factors, self.shape).tolist())
                if raveled_factors in list_permutations:
                    continue
                if len(set(raveled_factors)) != len(raveled_factors):
                    continue
                list_permutations.append(raveled_factors)

        assert self.validate_permutations(list_permutations)
        return list_permutations

    def validate_permutations(self, permutations):
        for prm in permutations:
            if len(set(prm)) != self.num:
                print(prm)
                print('not permutation')
                return False

        if len(set(permutations)) != len(permutations):
            print('not unique')
            print(permutations)
            return False

        return True


def is_same_lattice(H1, H2):
    M = np.linalg.solve(H1, H2)
    M_re = np.around(M).astype(np.int)

    if np.array_equal(np.dot(H1, M_re), H2):
        assert np.around(np.linalg.det(M_re) ** 2) == 1
        return True
    else:
        return False
