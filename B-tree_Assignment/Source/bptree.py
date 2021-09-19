import math
import sys
import csv
import pickle

NO_PARENT = -3
LEFTMOST = -2

# nonleaf 노드의 entry
class nonleaf_Entry:
    def __init__(self, key, child):
        self.key = key
        self.child = child

# leaf 노드의 entry
class leaf_Entry:
    def __init__(self, key, pointer: int):
        self.key = key
        self.pointer = pointer

class Node:
    def __init__(self, order):
        self.order = order # 자식 노드 최대 개수
        self.m = 0 # 현재 키 개수
        self.entries = [] # nonleaf entry 또는 leaf entry가 담기는 리스트
        self.right_node: Node = None # nonleaf 노드의 경우 가장 오른쪽 자식 노드, leaf노드의 경우 오른쪽 형제 노드
        self.prev_sibling: Node = None # leaf 노드의 왼쪽 형제 노드
        self.parent: Node = None # 부모 노드
        self.is_leaf: bool = True # 현재 노드의 leaf 여부
        self.p_idx = None # 현재 노드가 부모 노드의 몇 번째 인덱스에 위치하는지 저장

    # check if the node has been overflowed
    def is_overflow(self):
        if self.m == self.order:
            return True
        else:
            return False

    # key기준으로 오름차순 정렬해서 entry add
    # 키 중복으로 add실패할 경우 false반환
    def add(self, entry, idx) -> 'bool':
        # add 함수 호출 시 인덱스를 미리 알고 있는 경우 탐색 없이 바로 insert
        if idx != None:
            self.entries.insert(idx, entry)
            self.m += 1
            return True

        if self.m != 0:
            for i in range(self.m):
                if self.entries[i].key == entry.key:
                    return False # return false if the key has duplicated
                if self.entries[i].key > entry.key:
                    self.entries.insert(i, entry) #찾은 위치 i에 entry 삽입
                    self.m += 1
                    return True
        self.entries.append(entry) #맨 끝에 추가
        self.m += 1
        return True

### functions for insertion ###

    ## split overflowed leaf node, return the root node
    def split_leaf_node(self, root) -> 'Node':
    # split the node
        # 왼쪽 노드는 새로운 노드를 생성하고 오른쪽 노드는 기존 노드 활용, 키 개수 홀수일 때 오른쪽에 더 많은 키 할당됨

        # set the left node
        left_node = Node(self.order)
        mid = math.floor(self.order / 2)
        left_node.entries = self.entries[:mid] # 노드를 쪼개서 앞부분을 새로운 노드에
        left_node.m = mid # key 개수는 절반으로 줄어듦
        left_node.right_node = self # 원래 노드를 오른쪽 노드로 함
        left_node.parent = self.parent # 원래 노드의 부모 노드 가져오기
        if self.prev_sibling != None:
            self.prev_sibling.right_node = left_node
        left_node.prev_sibling = self.prev_sibling
        # set the right node
        del self.entries[:mid] # 원래 노드에서 앞부분 삭제
        self.m = self.order - mid # 홀수의 경우 오른쪽 노드의 키 개수가 더 많음
        self.prev_sibling = left_node

        # set the parent node
        # parent 노드 없어서 현재 노드 루트일 때
        if self.parent == None:
            new_root = Node(self.order) # 새로운 루트 생성
            new_root.is_leaf = False
            entry = nonleaf_Entry(self.entries[0].key, left_node)
            new_root.add(entry, None) # 새로운 루트 노드에 엔트리 넣기
            new_root.right_node = self # 새로운 루트 노드의 오른쪽 노드는 현재 노드
            self.parent = new_root # 부모 노드로 새로운 루트 연결
            left_node.parent = new_root
            return new_root # return the new root node 
    
        # parent 노드 있을 때
        else:
        # parent 노드로 키값 하나 올리고, 새로 만든 노드 연결해주기
            entry = nonleaf_Entry(self.entries[0].key, left_node) # set new entry for the parent node
            self.parent.add(entry, None) # add new entry in the parent node
            if self.parent.is_overflow(): # if parent has been overflowed, 
                return self.parent.split_nonleaf_node(root) # split the parent node (which is nonleaf node)
            return root

    # self 의 자식의 부모 노드를 node로 변경해주는 함수. nonleaf split과 nonleaf merge 과정에서 사용함
    # 1. 스플릿 과정에서 새로운 non leaf node가 생성될 수 있음 -> 새로운 노드가 갖고 있는 모든 자식 노드에 대하여 parent노드를 새로 만든 노드로 변경
    # 2. 병합되어 부모 노드가 없어진 자식 노드들을 병합시킨 노드로 연결
    def change_parent(self, node: 'Node'):
        for i in range(self.m):
            self.entries[i].child.parent = node
        self.right_node.parent = node

    ## split a nonleaf node, return the root node
    # nonleaf node의 split은 Btree와 동일한 로직으로 진행
    def split_nonleaf_node(self, root) -> 'Node':
        mid = math.floor((self.order - 1) / 2)
        mid_key = self.entries[mid].key
        # 왼쪽 노드는 새롭게 만들기
        left_node = Node(self.order) # 노드 생성
        left_node.entries = self.entries[:mid] # 노드에 엔트리 담기
        left_node.m = mid # 키 개수는 중앙 인덱스와 같음
        left_node.parent = self.parent # 부모 노드는 현재 노드의 것과 동일
        left_node.right_node = self.entries[mid].child # 오른쪽에는 현재 노드의 중앙 child를 가짐
        left_node.is_leaf = False
        left_node.change_parent(left_node) # 쪼개고 나서 아래에 있는 노드의 parent도 바꿔주기
        # 오른쪽 노드는 뒤에만 남김
        del self.entries[:(mid + 1)]
        self.m = math.floor(self.order / 2)

        # 루트 노드가 overflow되는 경우 새로운 루트 생성
        if self.parent == None:
            new_root = Node(self.order)
            new_root.is_leaf = False
            entry = nonleaf_Entry(mid_key, left_node)
            new_root.add(entry, None)
            new_root.right_node = self
            left_node.parent = new_root
            self.parent = new_root
            return new_root
        # 현재 루트 노드가 아닌 경우 그냥 parent노드에 적절히 add하고 오버플로우 여부 확인
        else:
            entry = nonleaf_Entry(mid_key, left_node)
            self.parent.add(entry, None)
            if self.parent.is_overflow():
                return self.parent.split_nonleaf_node(root)
            return root
    
### functions for deletion ###

    # 노드에서 받은 key에 해당하는 엔트리를 단순히 삭제하는 함수
    def simple_del(self, key):
        for i in range(self.m):
            if self.entries[i].key == key:
                del self.entries[i]
                self.m -= 1
                return

    # borrow entry from the right sibling node
    def borrow_right(self, key):
        self.add(self.right_node.entries[0], self.m) # 빌려와서 추가
        del self.right_node.entries[0] # 빌린 키 오른쪽 형제 노드에서 삭제해주기
        self.right_node.m -= 1 # 개수 하나 줄여주기

    # borrow entry from the left sibling node
    def borrow_left(self, key):
        self.add(self.prev_sibling.entries[-1], 0) # 빌려와서 추가
        del self.prev_sibling.entries[-1] # 빌린 키 왼쪽 형제 노드에서 삭제해주기
        self.prev_sibling.m -= 1 # 개수 하나 줄여주기

    ## get parent idx of the node
    # 현재 노드의 부모 노드 인덱스, 0번째 키보다 작거나 같은 첫번째 값의 인덱스 반환
    def get_parent_idx(self) -> 'int':
        if self.parent == None:
            return NO_PARENT
        if self.m == 0:
            return self.p_idx # 노드가 비어있기 전에 미리 계산해 둔 idx 값 반환
        if (self.is_leaf == True) & (self.prev_sibling == None): # 이 경우엔 무조건 맨 왼쪽 노드
            return LEFTMOST
        for i in range(self.parent.m - 1, -1, -1):
            if self.parent.entries[i].key <= self.entries[0].key:
                return i
        # 부모 노드의 맨 왼쪽 노드인 경우 
        return LEFTMOST

    ## merge leaf node (왼쪽으로 merge)
    def merge(self, p_idx, is_leftmost) -> 'Node':
        # 부모 노드의 왼쪽 끝 리프 노드가 아닌 경우 -> 왼쪽에 합치기
        if is_leftmost == False:
            # 해당 키 삭제하고 남은 엔트리 병합해주기
            for i in range(self.m):
                self.prev_sibling.add(self.entries[i], self.prev_sibling.m)
            # 리프 노드 링크 조정
            self.prev_sibling.right_node = self.right_node
            if self.right_node != None:
                self.right_node.prev_sibling = self.prev_sibling

            # 부모 노드의 오른쪽 끝 리프 노드인 경우
            if self.parent.right_node == self:
                if self.parent.m == 1: # 부모 노드가 비어있게 되는 경우 인덱스 미리 계산
                    self.parent.p_idx = self.parent.get_parent_idx()
                del self.parent.entries[p_idx]
                self.parent.m -= 1
                self.parent.right_node = self.prev_sibling # merge된 노드는 부모 노드의 맨 오른쪽 리프노드가 됨
            
            # 부모 노드의 맨 왼쪽도 아니고 오른쪽도 아닌 노드인 경우
            else:
                del self.parent.entries[p_idx + 1]
                self.parent.m -= 1
            ret = self.prev_sibling
                

        # 부모 노드의 맨 왼쪽 리프 노드일 경우 -> 오른쪽으로 merge
        else:
            # 오른쪽으로 병합하기
            for i in range(self.m):
                self.right_node.add(self.entries[i], i)
            # 리프 노드 링크 연결
            if self.prev_sibling != None:
                self.prev_sibling.right_node = self.right_node
            self.right_node.prev_sibling = self.prev_sibling
            if self.parent.m == 1: # 부모 노드가 비어 있게 될 경우 인덱스 미리 계산
                self.parent.p_idx = self.parent.get_parent_idx()
            del self.parent.entries[0] # 부모 노드의 맨 왼쪽 삭제
            self.parent.m -= 1
            ret = self.right_node
        del self
        return ret
    
    # index 키 재조정을 위해 가장 왼쪽 노드 첫번째 키값을 반환하는 함수
    def get_leftmost(self) -> 'int':
        n = self
        while n.is_leaf == False:
            if n.m == 0:
                return n.right_node.entries[0].key
            n = n.entries[0].child
        return n.entries[0].key

    # nonleaf node를 merge하는 함수
    def nonleaf_merge(self, root: 'Node'):
        lbound = math.ceil(self.order / 2) - 1
        p_idx = self.get_parent_idx()
        # 부모 노드의 맨 왼쪽 자식 노드가 아닌 경우 -> 왼쪽으로 merge
        if p_idx != LEFTMOST:
            # 병합되어 남아 있을 노드 l_node로 저장
            l_node = self.parent.entries[p_idx].child
            entry = nonleaf_Entry(self.parent.entries[p_idx].key, l_node.right_node)
            l_node.add(entry, l_node.m)
            for i in range(self.m):
                l_node.add(self.entries[i], l_node.m)
            l_node.right_node = self.right_node
            # 부모 노드가 비어있게 될 경우 자식 노드에서 부모 인덱스를 찾을 수 없으므로 미리 계산
            if self.parent.m == 1:
                self.parent.p_idx = self.parent.get_parent_idx()
            del self.parent.entries[p_idx]
            self.parent.m -= 1
            # 부모 노드의 맨 오른쪽 끝이라면
            if self.parent.right_node == self:
                self.parent.right_node = l_node
            # 그게 아니라면
            else:
                self.parent.entries[p_idx].child = l_node
            self.change_parent(l_node)
            # 루트가 바뀌는 경우
            if (self.parent == root) & (self.parent.m == 0):
                del self.parent
                l_node.parent = None
                root = l_node
            # 부모에서 빌려 와서 부모도 merge해야 하는 경우
            elif (self.parent != root) & (self.parent.m < lbound):
                root = self.parent.nonleaf_merge(root)
            # 병합 이후 노드가 오버플로우 된 경우 split
            if l_node.is_overflow():
                root = l_node.split_nonleaf_node(root)
            
        # 부모 노드의 맨 왼쪽 자식 노드인 경우 -> 오른쪽으로 merge
        else:
            # 병합되어 남아있을 노드 구해서 r_node로 저장
            if self.parent.m > 1:
                r_node = self.parent.entries[1].child
            else:
                r_node = self.parent.right_node
            # 부모 노드의 해당하는 키값 밑으로 내려서 병합하기. 키값 가져오고 자식 노드 연결 만들어주기
            entry = nonleaf_Entry(self.parent.entries[0].key, self.right_node)
            r_node.add(entry, 0)
            for i in range(self.m):
                r_node.add(self.entries[i], i)
            if self.parent.m == 1: # 부모 노드가 비어있게 될 경우 인덱스 미리 계산
                self.parent.p_idx = self.parent.get_parent_idx()
            del self.parent.entries[0]
            self.parent.m -= 1
            # 병합해서 사라질 노드의 자식 노드의 부모 노드를 새로운 노드로 바꿔주는 함수
            self.change_parent(r_node)
            # 루트가 바뀌는 경우
            if (self.parent == root) & (self.parent.m == 0):
                del self.parent
                r_node.parent = None
                root = r_node
            # 부모 노드가 루트가 아니면서 최소 키 개수를 만족하지 않을 때
            elif (self.parent != root) & (self.parent.m < lbound):
                root = self.parent.nonleaf_merge(root)
            # 병합 이후 노드가 오버플로우 된 경우 split
            if r_node.is_overflow():
                root = r_node.split_nonleaf_node(root)
        del self # 병합 완료된 노드는 삭제하기
        return root


class Bptree:
    def __init__(self, order):
        self.root = Node(order)
    
    ## get very first leaf node of the bplustree
    ## this is for saving the tree information in the index file.
    def get_first_leaf(self):
        n = self.root
        while n.is_leaf == False:
            n = n.entries[0].child
        return n

    def _find(self, key, node: Node):
        if node.is_leaf: # return if it is a leaf node
            return node
        
        for i in range(node.m):
            if key < node.entries[i].key:
                return self._find(key, node.entries[i].child)
        return self._find(key, node.right_node)
    
    def _find_del(self, key, node: Node):
        if node.is_leaf:
            for i in range(node.m):
                if node.entries[i].key == key:
                    return node
            return None # there's no key to be deleted
        for i in range(node.m):
            if key < node.entries[i].key:
                return self._find_del(key, node.entries[i].child)
        return self._find_del(key, node.right_node)
    
    ## insert key and value to the bptree
    def insert(self, key, value):
        leaf = self._find(key, self.root)
        entry = leaf_Entry(key, value)
        if leaf.add(entry, None) == False:
            print('Insertion Error (key : %d) : duplicated keys are not allowed!' %key)
            return

        if leaf.is_overflow():
            self.root = leaf.split_leaf_node(self.root)

    ## 삭제 이후에 인덱스 노드를 규칙에 맞게 재조정
    def _restruct_index(self, now: 'Node'):
        if now.is_leaf == False:
            if now.m == 0: # 아직 delete가 완료되지 않은 상태에는 빈 노드가 있을 수 있음
                return # 아래쪽에 더 이상 인덱스를 조정할 노드 없으므로 바로 리턴
            else: # 오른쪽 링크의, 자식 노드의, 가장 왼쪽 리프 노드의 첫번째 키로 인덱스 조정
                for i in range(now.m - 1):
                    now.entries[i].key = now.entries[i + 1].child.get_leftmost()
                now.entries[now.m - 1].key = now.right_node.get_leftmost()
            for i in range(now.m): # 쭉 내려가면서 트리의 인덱스 전부 조정
                self._restruct_index(now.entries[i].child)
            self._restruct_index(now.right_node)

    ## delete key from the bptree
    def delete(self, key):
        lbound = math.ceil(self.root.order / 2) - 1 # 노드의 최소 키 개수
        leaf = self._find_del(key, self.root) # 삭제할 키가 담긴 리프 노드 찾기
        if leaf == None: # 찾는 키가 트리에 없는 경우
            print('Deletion Error (key : %d) : no such key in the tree!' %key)
            return
        # 루트 하나만 있는 트리거나 리프 노드에 여유가 있는 경우
        if (leaf.m > lbound) or (leaf == self.root):
            leaf.simple_del(key)
            self._restruct_index(self.root)
            return
        # borrow (key rotation)
        if leaf.right_node != None:
            if leaf.right_node.m > lbound: # borrow from the right node
                leaf.simple_del(key)
                leaf.borrow_right(key)
                self._restruct_index(self.root)
                return 
        if leaf.prev_sibling != None:
            if leaf.prev_sibling.m > lbound: # borrow from the left node
                leaf.simple_del(key)
                leaf.borrow_left(key)
                self._restruct_index(self.root)
                return
        # borrow from the parent node
        p_idx = leaf.get_parent_idx() # 키 삭제 전에 노드 위치 정보 가져오기
        leaf.simple_del(key)
        ret = leaf.merge(p_idx, p_idx == LEFTMOST) # 현재 노드의 leaftmost 여부 boolean으로 전달
        self._restruct_index(self.root)
        # ret에는 병합 된 노드가 담겨 있음 (맨 왼쪽 노드였다면 오른쪽 형제 노드, 나머지 경우엔 왼쪽 형제 노드)
        # parent 노드가 루트이면서 남은 엔트리가 없는 경우
        if (ret.parent == self.root) & (ret.parent.m == 0):
            self.root = ret
            del ret.parent
        # parent 노드가 루트가 아니고 lbound 이하로 내려간 경우 
        elif (ret.parent != self.root) & (ret.parent.m < lbound):
            self.root = ret.parent.nonleaf_merge(self.root)
    
    # search a key from the bptree
    def search(self, key, node: Node):
        if node.is_leaf: #리프 노드이면 해당하는 키값 찾기
            for i in range(node.m):
                if key == node.entries[i].key: # 키값을 찾은 경우
                    print(node.entries[i].pointer) # pointer 값 (= value) 출력
                    return
            print('NOT FOUND') # 키값이 없는 경우
            return
        
        for i in range(node.m - 1):
            print(node.entries[i].key, end=',')
        print(node.entries[node.m - 1].key)
        
        for i in range(node.m):
            if key < node.entries[i].key:
                self.search(key, node.entries[i].child)
                return
        self.search(key, node.right_node)
    
    ## sub method for 'ranged_search'
    def print_to_end(self, node: 'Node', start_idx, end_key):
        # start index 부터 시작해서 end key보다 값이 작거나 같은 동안 키값을 출력하면서 오른쪽으로 이동
        i = start_idx
        while node != None:
            while i < node.m:
                if node.entries[i].key > end_key:
                    return
                print(node.entries[i].key , end='')
                print(',', end='')
                print(node.entries[i].pointer)
                i += 1
            node = node.right_node
            i = 0
            
    ## print the values of pointers to records having the keys within the range provided
    def ranged_search(self, start_key, end_key, node: 'Node'):
        if node.is_leaf: #리프 노드이면 해당하는 키값 찾기
            for i in range(node.m):
                if node.entries[i].key >= start_key: # 키값을 찾은 경우
                    self.print_to_end(node, i, end_key)
                    return
            # 다음 노드부터 봐야 하는 경우 (ex : 2부터 찾아야 하는데 현재 노드에 1까지 있음)
            self.print_to_end(node.right_node, 0, end_key)
            return
        
        for i in range(node.m):
            if start_key < node.entries[i].key:
                self.ranged_search(start_key, end_key, node.entries[i].child)
                return
        self.ranged_search(start_key, end_key, node.right_node)
    
    ## print tree (This function is for debuging)
    def print_tree(self, p):
        if p.is_leaf == False:
            for i in range(p.m):
                self.print_tree(p.entries[i].child)
                print(p.entries[i].key, end=' ')
            print()
            self.print_tree(p.right_node)
        else:
            for i in range(p.m):
                print(p.entries[i].key, end=' ')
            print()

## save information of the tree
class tree_info:
    def __init__(self, order):
        self.order = order
        self.l = []

    def make_list(self, first: 'Node'):
        self.l = [] # reset the list 
        n = first
        while n != None: # save all entries in ascending order
            self.l += n.entries
            n = n.right_node

def print_usage():
    print('usage: "-c index_file d" for creation')
    print('       "-i index_file data_file" for insertion')
    print('       "-d index_file data_file" for deletion')
    print('       "-s index_file key" for single key search')
    print('       "-r index_file start_key end_key" for ranged search')


if __name__ == '__main__':
    # argument number error -> exit immediately
    if len(sys.argv) < 4:
        print_usage()
        sys.exit()

    op = sys.argv[1]
    filename = sys.argv[2] # save index file name

    ## index file creation
    if op == '-c':
        order = sys.argv[3] # save order
        Tree = tree_info(int(order))
        with open(filename, "w+b") as index_file: # 인덱스 파일 쓰기 모드로 생성
            pickle.dump(Tree, index_file) # 직렬화해서 index file에 저장
    
    ## insertion
    elif op == '-i':
        data_file = sys.argv[3]
        with open(filename, "rb") as index_file: # 인덱스 파일 로드를 위해 읽기 모드로 열기
            Tree = pickle.load(index_file) # Tree 는 tree_info 클래스 객체
        
        # 저장된 정보로 현재까지의 비쁠트리 만들기
        bptree = Bptree(Tree.order)
        for i in range(int(len(Tree.l) / 2)):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        # 절반 나눠서 insert -> 트리 레벨 줄이기
        for i in range(len(Tree.l) - 1, int(len(Tree.l) / 2) - 1, -1):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        
        ## read input data file
        fd = open(data_file, 'r') # open the input data file (csv file)
        rdr = csv.reader(fd)
        for line in rdr:
            bptree.insert(int(line[0]), int(line[1])) # insert data
        fd.close()
        
        # 완성된 트리의 리프 노드 저장
        first_leaf = bptree.get_first_leaf()
        Tree.make_list(first_leaf)
        with open(filename, "w+b") as index_file: # 인덱스 파일 쓰기 모드로 열기, 기존 내용을 다 지우고 다시 쓴다
            pickle.dump(Tree, index_file) # 직렬화해서 index file에 저장
        
        del bptree

    ## deletion
    elif op == '-d':
        data_file = sys.argv[3]
        with open(filename, "rb") as index_file: # 인덱스 파일 로드를 위해 읽기 모드로 열기
            Tree = pickle.load(index_file) # Tree 는 tree_info 클래스 객체
        
        # 저장된 정보로 현재까지의 비쁠트리 만들기
        bptree = Bptree(Tree.order)
        for i in range(int(len(Tree.l) / 2)):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        
        for i in range(len(Tree.l) - 1, int(len(Tree.l) / 2) - 1, -1):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        
        # 현재 주어진 input파일 읽기
        fd = open(data_file, 'r') # open the input data file (csv file)
        rdr = csv.reader(fd)
        for line in rdr:
            bptree.delete(int(line[0]))
        fd.close()
    
        # 완성된 트리의 리프 노드 저장
        first_leaf = bptree.get_first_leaf()
        Tree.make_list(first_leaf)
        with open(filename, "w+b") as index_file: # 인덱스 파일 쓰기 모드로 열기, 기존 내용을 다 지우고 다시 쓴다
            pickle.dump(Tree, index_file) # 직렬화해서 index file에 저장
        
        del bptree

    ## single key search
    elif op == '-s':
        key = sys.argv[3] # key value to be found
        with open(filename, "rb") as index_file: # 인덱스 파일 로드를 위해 읽기 모드로 열기
            Tree = pickle.load(index_file)
        
        # 저장된 정보로 현재까지의 비쁠트리 만들기
        bptree = Bptree(Tree.order)
        for i in range(int(len(Tree.l) / 2)):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        
        for i in range(len(Tree.l) - 1, int(len(Tree.l) / 2) - 1, -1):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)

        bptree.search(int(key), bptree.root)

        del bptree
    
    ## ranged search
    elif op == '-r':
        start_key = sys.argv[3]
        end_key = sys.argv[4]
        with open(filename, "rb") as index_file: # 인덱스 파일 로드를 위해 읽기 모드로 열기
            Tree = pickle.load(index_file)

        # 저장된 정보로 현재까지의 비쁠트리 만들기
        bptree = Bptree(Tree.order)
        for i in range(int(len(Tree.l) / 2)):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
        
        for i in range(len(Tree.l) - 1, int(len(Tree.l) / 2) - 1, -1):
            bptree.insert(Tree.l[i].key, Tree.l[i].pointer)
            
        bptree.ranged_search(int(start_key), int(end_key), bptree.root)
        
        del bptree
    
    ## option error
    else:
        print_usage()