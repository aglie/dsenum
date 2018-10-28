import itertools

import numpy as np

from permutation import Permutation


class Labeling(object):

    def __init__(self, hnf, num_type, rotations=None):
        self.hnf = hnf
        self.num_type = num_type
        self.num_site = np.prod(self.hnf.diagonal())

        self.permutation = Permutation(self.hnf, rotations)
        # assuming that the 0-th element of permutaions is identity operation
        self.prm_t = self.permutation.get_translation_permutations()
        self.prm_all = self.permutation.get_symmetry_operation_permutaions()

    def act_permutation(self, labeling, prm):
        ret = tuple([labeling[prm[i]] for i in range(self.num_site)])
        return ret

    def convert_base(self, labeling):
        ret = np.sum([e * (self.num_type ** i)
                      for i, e in enumerate(labeling)])
        return ret

    def generate_possible_labelings(self):
        list_labelings = [lbl for lbl in itertools.product(range(self.num_type), repeat=self.num_site) if len(set(lbl)) == self.num_type]
        self.valid_flags = [True for _ in range(self.num_type ** self.num_site)]
        return list_labelings

    def is_representative_coloring(self, labeling):
        colors = []
        for e in labeling:
            if e not in colors:
                colors.append(e)

        if colors == sorted(colors):
            return True
        else:
            return False

    def remove_translation_and_exchanging_duplicates(self, labelings):
        unique_labelings = []
        for lbl in labelings:
            idx = self.convert_base(lbl)
            if not self.valid_flags[idx]:
                continue

            # remove superperiodic
            if any([(self.act_permutation(lbl, prm) == lbl) for prm in self.prm_t[1:]]):
                self.valid_flags[idx] = False
                continue

            # remove translation and exchanging duplicates
            for type_prm in itertools.permutations(range(self.num_type)):
                lbl_ex = [type_prm[e] for e in lbl]
                for prm in self.prm_t:
                    if (lbl_ex == lbl) and (prm == range(self.num_site)):
                        continue
                    operated_lbl_ex = self.act_permutation(lbl_ex, prm)
                    idx_lbl_ex = self.convert_base(operated_lbl_ex)
                    self.valid_flags[idx_lbl_ex] = False

            self.valid_flags[idx] = True
            unique_labelings.append(lbl)
        return unique_labelings

    def remove_rotation_duplicates(self, labelings):
        unique_labelings = []
        for lbl in labelings:
            idx = self.convert_base(lbl)
            if not self.valid_flags[idx]:
                continue

            for type_prm in itertools.permutations(range(self.num_type)):
                lbl_ex = [type_prm[e] for e in lbl]
                for prm in self.prm_all:
                    if (lbl_ex == lbl) and (prm == range(self.num_site)):
                        continue
                    operated_lbl_ex = self.act_permutation(lbl_ex, prm)
                    idx_lbl_ex = self.convert_base(operated_lbl_ex)
                    self.valid_flags[idx_lbl_ex] = False

            self.valid_flags[idx] = True
            unique_labelings.append(lbl)

        return unique_labelings

    def remove_duplicates(self, labelings):
        unique_labelings = self.remove_translation_and_exchanging_duplicates(labelings)
        unique_labelings = self.remove_rotation_duplicates(unique_labelings)
        return unique_labelings

    def get_inequivalent_labelings(self):
        labelings = self.generate_possible_labelings()
        labelings = self.remove_duplicates(labelings)
        # assert self.check_uniqueness(labelings)
        return labelings

    def check_uniqueness(self, labelings):
        for i, lbl in enumerate(labelings):
            for type_prm in itertools.permutations(range(self.num_type)):
                lbl_ex = [type_prm[e] for e in lbl]
                for prm in self.prm_all:
                    operated_lbl_ex = self.act_permutation(lbl_ex, prm)
                    try:
                        idx = labelings.index(operated_lbl_ex)
                    except ValueError:
                        continue

                    if idx != i:
                        return False
        return True


if __name__ == '__main__':
    hnf = np.array([[4]])
    num_type = 2
    labelings = Labeling(hnf, num_type)

    list_labelings = labelings.generate_possible_labelings()
    print('generate possible labelings')
    print(len(list_labelings))
    print(list_labelings)

    list_labelings = labelings.remove_duplicates(list_labelings)
    print('remove duplicates')
    print(len(list_labelings))
    print(list_labelings)
